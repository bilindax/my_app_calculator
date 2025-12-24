"""
AutoCAD Object Picker
====================
Handles selection and extraction of objects from AutoCAD via COM interface.
"""

import time
import math
from typing import List, Optional, Tuple
from bilind.models import Room, Opening, Wall

try:
    import win32com.client
    import pythoncom
except ImportError:
    raise ImportError("pywin32 is required. Install with: pip install pywin32")


class AutoCADPicker:
    """
    Handles AutoCAD object selection and dimension extraction.
    
    This class encapsulates all AutoCAD COM interface logic for picking
    rooms, doors, windows, and walls from the active drawing.
    """

    RPC_E_CALL_REJECTED = -2147418111
    _RETRY_DELAY = 0.35
    _MAX_RETRIES = 4
    _POINT_TOLERANCE = 1e-6
    
    def __init__(self, acad_app, doc):
        """
        Initialize the AutoCAD picker.
        
        Args:
            acad_app: AutoCAD application object
            doc: Active document object
        """
        self.acad = acad_app
        self.doc = doc
    
    def _delete_all_selections(self):
        """Clean up any existing selection sets."""
        try:
            for i in range(self.doc.SelectionSets.Count - 1, -1, -1):
                try:
                    self.doc.SelectionSets.Item(i).Delete()
                except:
                    pass
        except:
            pass

    def _is_call_rejected(self, err) -> bool:
        """Check if a COM error is RPC_E_CALL_REJECTED."""
        hresult = getattr(err, 'hresult', None)
        if hresult is None and getattr(err, 'args', None):
            hresult = err.args[0]
        return hresult == self.RPC_E_CALL_REJECTED

    def _create_selection_set(self, base_name: str):
        """Create a COM selection set with retry handling."""
        name = f"{base_name}_{int(time.time() * 1000) % 100000}"
        for attempt in range(self._MAX_RETRIES):
            try:
                return self.doc.SelectionSets.Add(name)
            except pythoncom.com_error as err:
                if self._is_call_rejected(err) and attempt < self._MAX_RETRIES - 1:
                    time.sleep(self._RETRY_DELAY * (attempt + 1))
                    pythoncom.PumpWaitingMessages()
                    continue
                raise

    def _select_on_screen(self, selection_set):
        """Invoke SelectOnScreen with retry to handle busy AutoCAD."""
        for attempt in range(self._MAX_RETRIES):
            try:
                selection_set.SelectOnScreen()
                return
            except pythoncom.com_error as err:
                if self._is_call_rejected(err) and attempt < self._MAX_RETRIES - 1:
                    time.sleep(self._RETRY_DELAY * (attempt + 1))
                    pythoncom.PumpWaitingMessages()
                    continue
                # Re-raise the original COM error so callers can catch it
                raise
            except Exception as e:
                # Catch any other exceptions
                raise Exception(f"Selection error: {str(e)}")
    
    def _get_bounding_box(self, obj) -> Tuple[Optional[float], Optional[float]]:
        """
        Extract width and length from object's bounding box.
        
        Args:
            obj: AutoCAD object
            
        Returns:
            Tuple of (width, length) or (None, None) if extraction fails
        """
        try:
            # Try VARIANT approach (some AutoCAD versions)
            min_variant = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, (0.0, 0.0, 0.0))
            max_variant = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, (0.0, 0.0, 0.0))
            obj.GetBoundingBox(min_variant, max_variant)
            minPt, maxPt = min_variant.value, max_variant.value
            
            if minPt and maxPt and len(minPt) >= 2 and len(maxPt) >= 2:
                w = abs(float(maxPt[0]) - float(minPt[0]))
                l = abs(float(maxPt[1]) - float(minPt[1]))
                if w > 0.001 and l > 0.001:
                    return w, l
        except:
            try:
                # Try direct approach (other AutoCAD versions)
                minPt, maxPt = [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
                obj.GetBoundingBox(minPt, maxPt)
                w = abs(float(maxPt[0]) - float(minPt[0]))
                l = abs(float(maxPt[1]) - float(minPt[1]))
                if w > 0.001 and l > 0.001:
                    return w, l
            except:
                pass
        
        return None, None
    
    def _estimate_dimensions_from_area(self, area: float, perimeter: float) -> Tuple[Optional[float], Optional[float]]:
        """
        Estimate width and length from area and perimeter using quadratic formula.
        
        For a rectangle: P = 2(w+l) and A = w*l
        Solving: w = (P/2 + sqrt((P/2)^2 - 4A)) / 2
        
        Args:
            area: Area in square units
            perimeter: Perimeter in linear units
            
        Returns:
            Tuple of (width, length) or (None, None) if calculation fails
        """
        if perimeter <= 0.001 or area <= 0.001:
            return None, None
        
        try:
            p_half = perimeter / 2
            discriminant = (p_half ** 2) - (4 * area)
            
            if discriminant >= 0:
                w = (p_half + math.sqrt(discriminant)) / 2
                l = area / w if w > 0.001 else 0
                
                if w > 0.001 and l > 0.001:
                    return w, l
        except:
            pass
        
        return None, None

    def _get_polyline_vertices(self, obj) -> List[Tuple[float, float]]:
        """Extract ordered XY vertices from a polyline-like AutoCAD object."""
        # Detect object type to determine coordinate stride
        obj_type = ""
        try:
            obj_type = str(getattr(obj, 'ObjectName', '')).upper()
        except:
            pass
        
        # LWPolyline uses XY pairs (stride 2), heavy polylines use XYZ (stride 3)
        is_lwpolyline = 'LWPOLYLINE' in obj_type or 'ACDBPOLYLINE' in obj_type
        is_heavy_polyline = '2DPOLYLINE' in obj_type or '3DPOLYLINE' in obj_type
        
        # Strategy 1 (BEST): NumberOfVertices + Coordinate() method
        # This is the most reliable as it gives us clean XY pairs directly
        try:
            count = int(getattr(obj, 'NumberOfVertices', 0))
            if count >= 3:
                coord_getter = getattr(obj, 'Coordinate', None)
                if callable(coord_getter):
                    vertices: List[Tuple[float, float]] = []
                    for idx in range(count):
                        try:
                            pt = coord_getter(idx)
                            if pt and len(pt) >= 2:
                                x = float(pt[0])
                                y = float(pt[1])
                                vertices.append((x, y))
                        except:
                            continue
                    if len(vertices) >= 3:
                        # Remove consecutive duplicates
                        cleaned = self._remove_duplicate_vertices(vertices)
                        if len(cleaned) >= 3:
                            return cleaned
        except Exception:
            pass

        # Strategy 2: Coordinates property with smart stride detection
        coord_sources: List[Tuple[List[float], int]] = []  # (coords, expected_stride)
        
        def _append_source(data, stride: int) -> None:
            if not data:
                return
            try:
                seq = list(data)
                if len(seq) >= 4:
                    coord_sources.append((seq, stride))
            except Exception:
                pass

        try:
            coords = getattr(obj, 'Coordinates', None)
            if coords is not None:
                expected_stride = 2 if is_lwpolyline else (3 if is_heavy_polyline else 2)
                _append_source(coords, expected_stride)
        except Exception:
            pass
        
        # Strategy 3: GetCoordinates method
        try:
            get_coords = getattr(obj, 'GetCoordinates', None)
            if callable(get_coords):
                expected_stride = 2 if is_lwpolyline else (3 if is_heavy_polyline else 2)
                _append_source(get_coords(), expected_stride)
        except Exception:
            pass

        if not coord_sources:
            return []

        def _build_vertices(seq: List[float], stride: int) -> List[Tuple[float, float]]:
            if stride < 2:
                stride = 2
            vertices: List[Tuple[float, float]] = []
            i = 0
            while i + 1 < len(seq):
                try:
                    x = float(seq[i])
                    y = float(seq[i + 1])
                    vertices.append((x, y))
                except Exception:
                    pass
                i += stride
            return self._remove_duplicate_vertices(vertices)

        # Try each source with its expected stride, pick the one with most vertices
        best_vertices: List[Tuple[float, float]] = []
        
        for raw_coords, expected_stride in coord_sources:
            # Try expected stride first
            verts = _build_vertices(raw_coords, expected_stride)
            if len(verts) > len(best_vertices):
                best_vertices = verts
            
            # Also try alternate stride in case object type detection was wrong
            alt_stride = 3 if expected_stride == 2 else 2
            alt_verts = _build_vertices(raw_coords, alt_stride)
            if len(alt_verts) > len(best_vertices):
                best_vertices = alt_verts

        return best_vertices

    def _remove_duplicate_vertices(self, vertices: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Remove consecutive duplicate vertices while preserving shape."""
        if not vertices:
            return []
        
        cleaned: List[Tuple[float, float]] = [vertices[0]]
        for pt in vertices[1:]:
            last = cleaned[-1]
            # Use a reasonable tolerance for construction drawings (1mm = 0.001m)
            if abs(pt[0] - last[0]) > 0.001 or abs(pt[1] - last[1]) > 0.001:
                cleaned.append(pt)
        
        return cleaned

    def _simplify_collinear_vertices(self, vertices: List[Tuple[float, float]], tol: float = 1e-6) -> List[Tuple[float, float]]:
        """Remove nearly-collinear intermediate points to recover true corners."""
        if not vertices or len(vertices) < 3:
            return vertices or []

        # Drop closing vertex if it repeats the first (common in polylines)
        pts = list(vertices)
        if len(pts) >= 2:
            x0, y0 = pts[0]
            xN, yN = pts[-1]
            if (abs(xN - x0) + abs(yN - y0)) <= tol:
                pts = pts[:-1]

        if len(pts) < 3:
            return pts

        def _is_collinear(a, b, c) -> bool:
            ax, ay = a
            bx, by = b
            cx, cy = c
            v1x, v1y = bx - ax, by - ay
            v2x, v2y = cx - bx, cy - by
            l1 = (v1x * v1x + v1y * v1y) ** 0.5
            l2 = (v2x * v2x + v2y * v2y) ** 0.5
            if l1 <= tol or l2 <= tol:
                return True
            cross = abs(v1x * v2y - v1y * v2x)
            # Normalized cross-product; ~0 means nearly collinear
            return (cross / (l1 * l2)) <= 1e-4

        simplified: List[Tuple[float, float]] = []
        n = len(pts)
        for i in range(n):
            prev_pt = pts[(i - 1) % n]
            cur_pt = pts[i]
            next_pt = pts[(i + 1) % n]
            if _is_collinear(prev_pt, cur_pt, next_pt):
                continue
            simplified.append(cur_pt)

        # If simplification removed too much, fall back
        return simplified if len(simplified) >= 3 else pts

    def _infer_rect_dims_from_vertices(self, vertices: List[Tuple[float, float]], scale: float) -> Tuple[Optional[float], Optional[float]]:
        """Infer (width, length) for (possibly rotated) rectangles; else return (None, None)."""
        import math

        pts = self._simplify_collinear_vertices(vertices)
        # Only handle rectangles (4 corners)
        if len(pts) != 4:
            return None, None

        # Build edge vectors/lengths
        edges = []
        for i in range(4):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % 4]
            dx, dy = (x2 - x1), (y2 - y1)
            ln = math.hypot(dx, dy)
            if ln <= 1e-9:
                return None, None
            edges.append((dx, dy, ln))

        # Check near-orthogonality for adjacent edges
        for i in range(4):
            dx1, dy1, l1 = edges[i]
            dx2, dy2, l2 = edges[(i + 1) % 4]
            dot = (dx1 * dx2 + dy1 * dy2)
            cos_abs = abs(dot) / (l1 * l2)
            if cos_abs > 0.2:  # ~78–102 degrees tolerance
                return None, None

        # Opposite edges should match in length (within tolerance)
        l0 = edges[0][2]
        l1 = edges[1][2]
        l2 = edges[2][2]
        l3 = edges[3][2]
        if (abs(l0 - l2) / max(l0, l2)) > 0.08:
            return None, None
        if (abs(l1 - l3) / max(l1, l3)) > 0.08:
            return None, None

        a = (l0 + l2) / 2.0
        b = (l1 + l3) / 2.0
        w = min(a, b) * scale
        l = max(a, b) * scale
        if w <= 0.001 or l <= 0.001:
            return None, None
        return w, l

    def _build_walls_from_polyline(self, obj, layer: str, scale: float, default_height: float) -> List[Wall]:
        """Convert a closed polyline into wall segments matching each edge."""
        vertices = self._get_polyline_vertices(obj)
        
        # Need at least 3 unique vertices for a closed shape
        if len(vertices) < 3:
            return []

        is_closed = False
        try:
            is_closed = bool(getattr(obj, 'Closed', False))
        except Exception:
            pass
        
        # Check if first and last points are close (looser tolerance for real-world drawings)
        if not is_closed and len(vertices) >= 3:
            first, last = vertices[0], vertices[-1]
            dist = math.hypot(last[0] - first[0], last[1] - first[1])
            # Use 10mm tolerance for checking if polyline is virtually closed
            if dist < 0.01:
                is_closed = True

        if not is_closed:
            return []

        # Build walls from each edge
        # For a closed polyline with N vertices, we have N edges
        # Edge i connects vertex[i] to vertex[(i+1) % N]
        height = float(default_height or 0.0)
        if height <= 0:
            height = 3.0

        walls: List[Wall] = []
        min_length = 0.01  # 1cm minimum wall length after scaling
        n = len(vertices)
        
        for idx in range(n):
            x1, y1 = vertices[idx]
            x2, y2 = vertices[(idx + 1) % n]  # Wrap around to first vertex for last edge
            length_raw = math.hypot(x2 - x1, y2 - y1)
            length = length_raw * scale
            
            if length <= min_length:
                continue
                
            wall = Wall(
                name=f"Wall {len(walls) + 1}",
                layer=layer,
                length=length,
                height=height
            )
            walls.append(wall)

        return walls
    
    def pick_rooms(self, scale: float = 1.0, start_index: int = 1, room_type: str = "Other", **kwargs) -> List[Room]:
        """Pick closed shapes in AutoCAD and convert them into Room models."""

        self._delete_all_selections()
        prompt_text = f"Select ROOMS ({room_type}):" if room_type != "Other" else "Select ROOMS (closed polylines/hatches):"
        self.acad.prompt(prompt_text)

        rooms: List[Room] = []
        default_wall_height = float(kwargs.get('default_wall_height', 0.0) or 3.0)
        # Get existing rooms from project to avoid duplicate names
        existing_rooms = kwargs.get('existing_rooms', [])
        ss = self._create_selection_set("BILIND_ROOMS")
        try:
            self._select_on_screen(ss)
            for i in range(ss.Count):
                try:
                    obj = ss.Item(i)
                except Exception:
                    continue

                try:
                    area_du = float(obj.Area)
                except Exception:
                    continue

                if area_du <= 0.0001:
                    continue

                try:
                    perim_du = float(obj.Length)
                except Exception:
                    try:
                        # Try Perimeter property (common for Regions/Hatches)
                        perim_du = float(obj.Perimeter)
                    except Exception:
                        perim_du = 0.0

                try:
                    layer = str(obj.Layer)
                except Exception:
                    layer = "Unknown"

                # Derive width/length:
                # - If the shape is a (possibly rotated) rectangle, use its true edge lengths.
                # - If it's irregular (more than 4 corners), leave width/length unset so exports show wall-length sums.
                width, length = None, None
                verts = self._get_polyline_vertices(obj)
                if verts:
                    width, length = self._infer_rect_dims_from_vertices(verts, scale)

                if width is None or length is None:
                    w_du, l_du = self._get_bounding_box(obj)
                    if w_du and l_du:
                        # Bounding box in world axes (ok as last resort)
                        w_bb = w_du * scale
                        l_bb = l_du * scale
                        # Normalize so length is the larger value for readability
                        width = min(w_bb, l_bb)
                        length = max(w_bb, l_bb)
                    else:
                        # Fall back to estimating from area/perimeter in scaled units
                        width, length = self._estimate_dimensions_from_area(
                            area_du * scale * scale,
                            perim_du * scale
                        )

                # If still not reliable, unset
                if not width or not length or width <= 0.001 or length <= 0.001:
                    width, length = None, None

                try:
                    name_idx = start_index + len(rooms)
                    # Use room_type as default name instead of generic "Room1"
                    if room_type and room_type != "Other" and room_type != "[Not Set]":
                        # Count how many of this type already exist in BOTH existing project rooms AND current batch
                        existing_type_count = sum(1 for r in existing_rooms if (
                            r.get('room_type') if isinstance(r, dict) else getattr(r, 'room_type', None)
                        ) == room_type)
                        current_batch_count = sum(1 for r in rooms if r.room_type == room_type)
                        type_count = existing_type_count + current_batch_count + 1
                        default_name = f"{room_type} {type_count}"
                    else:
                        default_name = f"Room{name_idx}"
                    
                    room = Room(
                        name=default_name,
                        layer=layer,
                        area=area_du * scale * scale,
                        perimeter=perim_du * scale,
                        width=width,
                        length=length,
                        room_type=room_type  # Assign room type
                    )
                except ValueError:
                    continue
                except Exception:
                    continue

                wall_segments = self._build_walls_from_polyline(obj, layer, scale, default_wall_height)
                if wall_segments:
                    room.walls = wall_segments
                    room.wall_segments = [
                        {'length': w.length, 'height': w.height}
                        for w in wall_segments
                    ]
                    if not room.wall_height:
                        room.wall_height = wall_segments[0].height
                    
                    # If perimeter was 0 (e.g. Hatch without Perimeter prop), calculate from walls
                    if room.perimeter <= 0.001:
                        room.perimeter = sum(w.length for w in wall_segments)

                rooms.append(room)
        finally:
            try:
                ss.Delete()
            except Exception:
                pass

        return rooms
    
    def pick_walls(self, scale: float = 1.0, height: float = 3.0, start_index: int = 1, **kwargs) -> List[Wall]:
        """Pick linear elements in AutoCAD and convert them into Wall models."""

        self._delete_all_selections()
        self.acad.prompt(f"Select WALLS (lines/polylines) - Height: {height}m:")

        walls: List[Wall] = []
        ss = self._create_selection_set("BILIND_WALL")
        try:
            self._select_on_screen(ss)
            for i in range(ss.Count):
                try:
                    obj = ss.Item(i)
                except Exception:
                    continue

                # Try multiple ways to read linear length
                length_du = None
                try:
                    length_du = float(getattr(obj, 'Length'))
                except Exception:
                    pass
                if length_du is None or length_du <= 0:
                    try:
                        length_du = float(getattr(obj, 'ArcLength'))
                    except Exception:
                        length_du = None
                if length_du is None:
                    # Unsupported object for wall picking, skip
                    continue

                if length_du <= 0.001:
                    continue

                length = length_du * scale

                try:
                    layer = str(obj.Layer)
                except Exception:
                    layer = "Unknown"

                try:
                    name_idx = start_index + len(walls)
                    wall = Wall(
                        name=f"Wall{name_idx}",
                        layer=layer,
                        length=length,
                        height=height
                    )
                except ValueError:
                    continue
                except Exception:
                    continue

                walls.append(wall)
        finally:
            try:
                ss.Delete()
            except Exception:
                pass

        return walls
    
    def count_openings(self, opening_type: str, **kwargs) -> int:
        """
        Count door or window blocks selected in AutoCAD.
        
        Args:
            opening_type: 'DOOR' or 'WINDOW'
            
        Returns:
            Number of blocks selected
        """
        self._delete_all_selections()
        
        self.acad.prompt(f"Select {opening_type.upper()}S (any blocks):")
        
        ss = self._create_selection_set(f"BILIND_{opening_type}")
        try:
            self._select_on_screen(ss)
            count = ss.Count
        finally:
            try:
                ss.Delete()
            except Exception:
                pass
        
        return count

    def pick_openings(self, opening_type: str, scale: float = 1.0, start_index: int = 1, **kwargs) -> List[Opening]:
        """Pick door/window blocks in AutoCAD and convert them into Opening models."""

        self._delete_all_selections()
        self.acad.prompt(f"Select {opening_type.upper()}S (BLOCKS only):")

        openings: List[Opening] = []
        ss = self._create_selection_set(f"BILIND_{opening_type}_PICK")
        try:
            self._select_on_screen(ss)
            for i in range(ss.Count):
                try:
                    block = ss.Item(i)
                except Exception:
                    continue

                try:
                    obj_type = str(block.ObjectName)
                    if "BlockReference" not in obj_type:
                        continue
                except Exception:
                    continue

                width_raw, height_raw = None, None

                # Priority 1: dynamic block properties
                try:
                    if hasattr(block, "IsDynamicBlock") and block.IsDynamicBlock:
                        props = block.GetDynamicBlockProperties()
                        for prop in props:
                            name_upper = str(prop.PropertyName).upper()
                            value = prop.Value
                            if name_upper in {"WIDTH", "W", "DOOR WIDTH", "WINDOW WIDTH"} and (width_raw is None or width_raw <= 0.001):
                                width_raw = abs(float(value))
                            elif name_upper in {"HEIGHT", "H", "DOOR HEIGHT", "WINDOW HEIGHT"} and (height_raw is None or height_raw <= 0.001):
                                height_raw = abs(float(value))
                except Exception:
                    pass

                # Priority 2: block attributes
                if width_raw is None or height_raw is None:
                    try:
                        if getattr(block, "HasAttributes", False):
                            for att in block.GetAttributes():
                                tag = str(att.TagString).upper()
                                val = str(att.TextString)
                                if (width_raw is None or width_raw <= 0.001) and tag in {"WIDTH", "W"}:
                                    try:
                                        width_raw = abs(float(val))
                                    except Exception:
                                        pass
                                elif (height_raw is None or height_raw <= 0.001) and tag in {"HEIGHT", "H"}:
                                    try:
                                        height_raw = abs(float(val))
                                    except Exception:
                                        pass
                    except Exception:
                        pass

                # Priority 3: bounding box
                if width_raw is None or height_raw is None or width_raw <= 0.001 or height_raw <= 0.001:
                    try:
                        min_pt, max_pt = [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
                        block.GetBoundingBox(min_pt, max_pt)
                        bbox_w = abs(max_pt[0] - min_pt[0])
                        bbox_h = abs(max_pt[1] - min_pt[1])
                        if (width_raw is None or width_raw <= 0.001) and bbox_w > 0.001:
                            width_raw = bbox_w
                        if (height_raw is None or height_raw <= 0.001) and bbox_h > 0.001:
                            height_raw = bbox_h
                    except Exception:
                        pass

                if not width_raw or not height_raw or width_raw <= 0.001 or height_raw <= 0.001:
                    continue

                layer = str(block.Layer) if hasattr(block, "Layer") else "Unknown"
                width = width_raw * scale
                height = height_raw * scale
                prefix = "D" if opening_type == "DOOR" else "W"
                base_name = f"{prefix}{start_index + len(openings)}"
                type_label = str(getattr(block, "EffectiveName", "") or getattr(block, "Name", "")) or "AutoCAD Block"

                try:
                    opening = Opening(
                        name=base_name,
                        opening_type=opening_type,
                        material_type=type_label,
                        layer=layer,
                        width=width,
                        height=height,
                        quantity=1
                    )
                except ValueError:
                    continue
                except Exception:
                    continue

                openings.append(opening)
        finally:
            try:
                ss.Delete()
            except Exception:
                pass

        return openings
