"""
Room-Opening Association Manager
=================================
Manages the relationship between rooms and their openings (doors/windows).
"""

from typing import List, Dict, Any, Optional, Set, Tuple


class RoomOpeningAssociation:
    """
    Manages associations between rooms and openings.
    
    Responsibilities:
    - Track which openings belong to which rooms
    - Calculate total opening areas per room
    - Validate assignments (no duplicates, all assigned)
    - Provide helper methods for UI and calculations
    """
    
    def __init__(self, rooms: List[Dict], doors: List[Dict], windows: List[Dict]):
        """
        Initialize the association manager.
        
        Args:
            rooms: Reference to main rooms list
            doors: Reference to main doors list
            windows: Reference to main windows list
        """
        self.rooms = rooms
        self.doors = doors
        self.windows = windows
    
    def get_opening_by_id(self, opening_id: str) -> Optional[Dict[str, Any]]:
        """
        Get door or window by ID.
        
        Args:
            opening_id: Name/ID of the opening (e.g., 'D1', 'W2')
        
        Returns:
            Opening dictionary or None if not found
        """
        for door in self.doors:
            name = door.get('name') if isinstance(door, dict) else getattr(door, 'name', None)
            if name == opening_id:
                return door
        
        for window in self.windows:
            name = window.get('name') if isinstance(window, dict) else getattr(window, 'name', None)
            if name == opening_id:
                return window
        
        return None
    
    def get_room_opening_ids(self, room: Dict[str, Any]) -> List[str]:
        """
        Get list of opening IDs assigned to a room.
        
        Args:
            room: Room dictionary
        
        Returns:
            List of opening IDs (e.g., ['D1', 'W1', 'W2'])
        """
        if hasattr(room, 'opening_ids'):
            opening_ids = getattr(room, 'opening_ids', []) or []
            return list(opening_ids)
        return room.get('opening_ids', [])
    
    def set_room_opening_ids(self, room: Dict[str, Any], opening_ids: List[str]) -> None:
        """
        Set the opening IDs for a room and update cached area.
        
        Args:
            room: Room dictionary
            opening_ids: List of opening IDs to assign
        """
        if hasattr(room, 'opening_ids'):
            setattr(room, 'opening_ids', opening_ids)
            setattr(room, 'opening_total_area', self.calculate_room_opening_area(room))
        else:
            room['opening_ids'] = opening_ids
            room['opening_total_area'] = self.calculate_room_opening_area(room)
    
    def calculate_room_opening_area(self, room: Dict[str, Any]) -> float:
        """
        Calculate total area of all openings in a room.
        
        Args:
            room: Room dictionary
        
        Returns:
            Total area in m²
        """
        total = 0.0
        room_name = (room.get('name') if isinstance(room, dict) else getattr(room, 'name', None)) or ''
        # Gather openings by room either via room.opening_ids or opening.assigned_rooms
        opening_ids = set(self.get_room_opening_ids(room))
        # Add those that list this room in assigned_rooms
        for seq in (self.doors, self.windows):
            for o in seq:
                try:
                    name = (o.get('name') if isinstance(o, dict) else getattr(o, 'name', None))
                    if not name:
                        continue
                    assigned = (o.get('assigned_rooms') if isinstance(o, dict) else getattr(o, 'assigned_rooms', [])) or []
                    if room_name and room_name in assigned:
                        opening_ids.add(name)
                except Exception:
                    continue

        for opening_id in opening_ids:
            opening = self.get_opening_by_id(opening_id)
            if not opening:
                continue
            # Compute share factor for this room
            share = self._compute_share_for_room(opening, room_name)
            if share <= 0:
                continue
            
            if hasattr(opening, 'area'):
                area_val = float(getattr(opening, 'area', 0.0) or 0.0)
                room_qtys = getattr(opening, 'room_quantities', {}) or {}
            else:
                area_val = float(opening.get('area', 0.0) or 0.0)
                room_qtys = opening.get('room_quantities', {}) or {}
            
            # Multiply by quantity in this room (default 1 if assigned)
            qty = int(room_qtys.get(room_name, 1))
            total += area_val * share * qty
        return total

    def _rooms_containing_opening(self, opening_id: str) -> List[str]:
        """Return list of room names that reference this opening in opening_ids."""
        result: List[str] = []
        for r in self.rooms:
            rname = (r.get('name') if isinstance(r, dict) else getattr(r, 'name', None)) or ''
            ids = self.get_room_opening_ids(r) or []
            if opening_id in ids:
                result.append(rname)
        return result

    def _resolve_opening_room_list(self, opening_id: str, assigned_side: List[str]) -> List[str]:
        """Combine assigned_rooms + room.opening_ids references without duplicates."""
        combined: List[str] = []
        seen: Set[str] = set()
        sources = [assigned_side or [], self._rooms_containing_opening(opening_id)]
        for source in sources:
            for room_name in source:
                if not room_name:
                    continue
                if room_name not in seen:
                    seen.add(room_name)
                    combined.append(room_name)
        return combined

    def _compute_share_for_room(self, opening: Any, room_name: str) -> float:
        """Compute how much of an opening's area to attribute to a given room.

        Rules:
        - If opening.room_shares provided, use it.
        - Else if opening.assigned_rooms provided: 'split' -> equal share; 'single' -> 1 for first/primary, 0 otherwise; 'custom' -> equal if no map.
        - Else if duplicates in room.opening_ids across rooms: equal split among duplicates.
        - Else: 1.0
        """
        try:
            # Extract fields
            if isinstance(opening, dict):
                opening_id = opening.get('name') or opening.get('id')
                assigned = opening.get('assigned_rooms') or []
                shares = opening.get('room_shares') or {}
                mode = opening.get('share_mode') or None
                area_val = float(opening.get('area', 0.0) or 0.0)
            else:
                opening_id = getattr(opening, 'name', None) or getattr(opening, 'id', None)
                assigned = getattr(opening, 'assigned_rooms', []) or []
                shares = getattr(opening, 'room_shares', None) or {}
                mode = getattr(opening, 'share_mode', None)
                area_val = float(getattr(opening, 'area', 0.0) or 0.0)

            if not opening_id or area_val <= 0.0 or not room_name:
                return 0.0

            # Explicit per-room shares override
            if shares:
                return float(shares.get(room_name, 0.0) or 0.0)

            # Assigned rooms logic
            if assigned:
                if room_name not in assigned:
                    return 0.0
                if (mode or 'split') == 'split':
                    return 1.0 / max(1, len(assigned))
                if mode == 'single':
                    # Attribute full to the first assigned room
                    return 1.0 if room_name == assigned[0] else 0.0
                if mode == 'custom':
                    # No shares provided -> fallback to equal split
                    return 1.0 / max(1, len(assigned))

            # Fallback: check duplicates in room.opening_ids
            dup_rooms = self._rooms_containing_opening(opening_id)
            if dup_rooms:
                if room_name not in dup_rooms:
                    return 0.0
                return 1.0 / max(1, len(dup_rooms))

            # Default: full attribution
            return 1.0
        except Exception:
            return 0.0
    
    def get_room_net_wall_area(self, room: Dict[str, Any], wall_height: float = 3.0) -> float:
        """
        Calculate net wall area for a room (perimeter × height - openings).
        
        Args:
            room: Room dictionary
            wall_height: Height of walls in meters (default 3.0)
        
        Returns:
            Net wall area in m²
        """
        if hasattr(room, 'perimeter'):
            perimeter = float(getattr(room, 'perimeter', 0.0) or 0.0)
        else:
            perimeter = float(room.get('perim', 0.0) or 0.0)
        gross_area = perimeter * wall_height
        opening_area = self.calculate_room_opening_area(room)
        return max(0.0, gross_area - opening_area)
    
    def validate_assignments(self) -> Tuple[bool, str]:
        """
        Validate all room-opening assignments.
        
        Checks:
        - No opening assigned to multiple rooms
        - Optionally warn about unassigned openings
        
        Returns:
            Tuple of (is_valid, message)
        """
        assigned = set()
        duplicates = []
        
        for room in self.rooms:
            for opening_id in self.get_room_opening_ids(room):
                if opening_id in assigned:
                    duplicates.append(opening_id)
                assigned.add(opening_id)
        
        if duplicates:
            return False, f"❌ Error: {', '.join(duplicates)} assigned to multiple rooms"
        
        # Check for unassigned openings (support dicts and dataclasses)
        def _name_set(seq):
            result = set()
            for o in seq:
                if isinstance(o, dict):
                    n = o.get('name')
                else:
                    n = getattr(o, 'name', None)
                if n:
                    result.add(n)
            return result
        all_openings = _name_set(self.doors) | _name_set(self.windows)
        unassigned = all_openings - assigned
        
        if unassigned:
            return True, f"⚠️ Warning: Unassigned openings: {', '.join(sorted(unassigned))}"
        
        return True, "✓ All openings properly assigned"
    
    def get_room_by_opening_id(self, opening_id: str) -> Optional[Dict[str, Any]]:
        """
        Find which room an opening is assigned to.
        
        Args:
            opening_id: Opening ID to search for
        
        Returns:
            Room dictionary or None if not assigned
        """
        for room in self.rooms:
            if opening_id in self.get_room_opening_ids(room):
                return room
        return None
    
    def unassign_opening(self, opening_id: str) -> bool:
        """
        Remove an opening from its assigned room.
        
        Args:
            opening_id: Opening ID to unassign
        
        Returns:
            True if opening was found and removed, False otherwise
        """
        room = self.get_room_by_opening_id(opening_id)
        if room:
            opening_ids = self.get_room_opening_ids(room)
            opening_ids.remove(opening_id)
            self.set_room_opening_ids(room, opening_ids)
            return True
        return False
    
    def get_all_assignments(self) -> Dict[str, List[str]]:
        """
        Get all room-opening assignments.
        
        Returns:
            Dictionary mapping room names to lists of opening IDs
        """
        assignments = {}
        for room in self.rooms:
            if hasattr(room, 'name'):
                room_name = getattr(room, 'name', 'Unknown') or 'Unknown'
            else:
                room_name = room.get('name', 'Unknown')
            assignments[room_name] = self.get_room_opening_ids(room)
        return assignments
    
    def format_opening_list(self, room: Dict[str, Any], max_items: int = 5) -> str:
        """
        Format opening IDs for display (e.g., "D1,W1,W2" or "D1,D2,... +3 more").
        
        Args:
            room: Room dictionary
            max_items: Maximum items to show before truncating
        
        Returns:
            Formatted string
        """
        opening_ids = self.get_room_opening_ids(room)
        if not opening_ids:
            return '-'
        
        if len(opening_ids) <= max_items:
            return ','.join(opening_ids)
        
        shown = ','.join(opening_ids[:max_items])
        remaining = len(opening_ids) - max_items
        return f"{shown},... +{remaining} more"
    
    def migrate_legacy_rooms(self) -> int:
        """
        Add 'opening_ids' and 'opening_total_area' fields to rooms that don't have them.
        
        Returns:
            Number of rooms migrated
        """
        migrated = 0
        for room in self.rooms:
            if isinstance(room, dict) and 'opening_ids' not in room:
                room['opening_ids'] = []
                room['opening_total_area'] = 0.0
                migrated += 1
        return migrated

    def get_summary_for_room(self, room: Dict[str, Any], max_items: int = 5) -> str:
        """Return a human-readable summary of openings assigned to a room."""
        return self.format_opening_list(room, max_items)
    
    def get_summary_dict_for_room(self, room: Dict[str, Any]) -> Dict[str, Any]:
        """
        Return a dictionary with opening details for a room.
        
        Returns:
            Dictionary with door_ids, window_ids, door_count, window_count
        """
        door_ids = []
        window_ids = []
        
        for opening in self.doors:
            if self._is_opening_in_room(opening, room):
                name = opening.get('name') if isinstance(opening, dict) else getattr(opening, 'name', '')
                if name:
                    door_ids.append(name)
        
        for opening in self.windows:
            if self._is_opening_in_room(opening, room):
                name = opening.get('name') if isinstance(opening, dict) else getattr(opening, 'name', '')
                if name:
                    window_ids.append(name)
        
        return {
            'door_ids': door_ids,
            'window_ids': window_ids,
            'door_count': len(door_ids),
            'window_count': len(window_ids)
        }

    def _is_opening_in_room(self, opening: Any, room: Dict[str, Any]) -> bool:
        """Determine whether an opening belongs to a room.

        Supports both legacy dict records and dataclass model instances.
        Membership can be defined in either:
        - Opening.assigned_rooms (list of room names)
        - Room.opening_ids (list of opening names)

        Args:
            opening: Door/window record (dict or model instance)
            room: Room record (dict or model instance)

        Returns:
            True if opening is assigned to the room.
        """
        try:
            # Extract names safely
            if isinstance(room, dict):
                room_name = room.get('name') or room.get('id')
            else:
                room_name = getattr(room, 'name', None) or getattr(room, 'id', None)

            if isinstance(opening, dict):
                opening_name = opening.get('name') or opening.get('id')
                assigned_rooms = opening.get('assigned_rooms') or []
            else:
                opening_name = getattr(opening, 'name', None) or getattr(opening, 'id', None)
                assigned_rooms = getattr(opening, 'assigned_rooms', []) or []

            if not room_name or not opening_name:
                return False

            # Check opening's assigned rooms list
            if assigned_rooms and room_name in assigned_rooms:
                return True

            # Fallback: check room's opening_ids list
            opening_ids = self.get_room_opening_ids(room)
            if opening_ids and opening_name in opening_ids:
                return True

            return False
        except Exception:
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about room-opening assignments.
        
        Returns:
            Dictionary with stats (total_rooms, rooms_with_openings, etc.)
        """
        total_rooms = len(self.rooms)
        total_openings = len(self.doors) + len(self.windows)
        
        rooms_with_openings = sum(1 for r in self.rooms if self.get_room_opening_ids(r))
        
        all_assigned = set()
        for room in self.rooms:
            all_assigned.update(self.get_room_opening_ids(room))
        
        assigned_openings = len(all_assigned)
        unassigned_openings = total_openings - assigned_openings
        
        return {
            'total_rooms': total_rooms,
            'total_openings': total_openings,
            'rooms_with_openings': rooms_with_openings,
            'assigned_openings': assigned_openings,
            'unassigned_openings': unassigned_openings
        }
    
    def get_opening_counts(self) -> Dict[str, Any]:
        """
        Get actual vs appearance counts for doors and windows.
        
        An opening shared between 2 rooms appears twice in room lists,
        but should be counted once for material/quantity purposes.
        
        Returns:
            Dictionary with:
            - actual_doors: Unique door count (physical doors)
            - actual_windows: Unique window count (physical windows)
            - appearance_doors: Sum of doors across all rooms (may double-count shared)
            - appearance_windows: Sum of windows across all rooms
            - shared_doors: Doors assigned to multiple rooms
            - shared_windows: Windows assigned to multiple rooms
            - door_details: List of {name, qty, rooms, area}
            - window_details: List of {name, qty, rooms, area}
        """
        # Actual counts (unique openings)
        actual_doors = len(self.doors)
        actual_windows = len(self.windows)
        
        # Track appearance counts and shared openings
        door_details = []
        window_details = []
        shared_doors = 0
        shared_windows = 0
        appearance_doors = 0
        appearance_windows = 0
        
        # Process doors
        for door in self.doors:
            if isinstance(door, dict):
                name = door.get('name', '')
                qty = int(door.get('qty', 1) or door.get('quantity', 1) or 1)
                area = float(door.get('area', 0.0) or 0.0)
                assigned = door.get('assigned_rooms', []) or []
                room_qtys = door.get('room_quantities', {}) or {}
            else:
                name = getattr(door, 'name', '')
                qty = int(getattr(door, 'qty', 1) or getattr(door, 'quantity', 1) or 1)
                area = float(getattr(door, 'area', 0.0) or 0.0)
                assigned = getattr(door, 'assigned_rooms', []) or []
                room_qtys = getattr(door, 'room_quantities', {}) or {}
            
            rooms = self._resolve_opening_room_list(name, assigned)
            room_count = len(rooms) if rooms else 1
            if room_count > 1:
                shared_doors += 1
            
            # Calculate appearance: sum of room_quantities OR qty × rooms as fallback
            if room_qtys:
                appearance_doors += sum(room_qtys.values())
            else:
                appearance_doors += room_count * qty
            
            door_details.append({
                'name': name,
                'qty': qty,
                'rooms': rooms,
                'room_count': room_count,
                'area': area,
                'is_shared': room_count > 1,
                'room_quantities': room_qtys
            })
        
        # Process windows
        for window in self.windows:
            if isinstance(window, dict):
                name = window.get('name', '')
                qty = int(window.get('qty', 1) or window.get('quantity', 1) or 1)
                area = float(window.get('area', 0.0) or 0.0)
                assigned = window.get('assigned_rooms', []) or []
                room_qtys = window.get('room_quantities', {}) or {}
            else:
                name = getattr(window, 'name', '')
                qty = int(getattr(window, 'qty', 1) or getattr(window, 'quantity', 1) or 1)
                area = float(getattr(window, 'area', 0.0) or 0.0)
                assigned = getattr(window, 'assigned_rooms', []) or []
                room_qtys = getattr(window, 'room_quantities', {}) or {}
            
            rooms = self._resolve_opening_room_list(name, assigned)
            room_count = len(rooms) if rooms else 1
            if room_count > 1:
                shared_windows += 1
            
            # Calculate appearance: sum of room_quantities OR qty × rooms as fallback
            if room_qtys:
                appearance_windows += sum(room_qtys.values())
            else:
                appearance_windows += room_count * qty
            
            window_details.append({
                'name': name,
                'qty': qty,
                'rooms': rooms,
                'room_count': room_count,
                'area': area,
                'is_shared': room_count > 1,
                'room_quantities': room_qtys
            })
        
        # Calculate total quantities (actual physical count)
        total_door_qty = sum(d['qty'] for d in door_details)
        total_window_qty = sum(w['qty'] for w in window_details)
        
        return {
            'actual_doors': actual_doors,
            'actual_windows': actual_windows,
            'total_door_qty': total_door_qty,
            'total_window_qty': total_window_qty,
            'appearance_doors': appearance_doors,
            'appearance_windows': appearance_windows,
            'shared_doors': shared_doors,
            'shared_windows': shared_windows,
            'door_details': door_details,
            'window_details': window_details
        }

    def assign_opening_to_rooms(self, opening_id: str, room_names: List[str], mode: str = 'add') -> int:
        """Assign an opening to multiple rooms, updating both sides.

        Args:
            opening_id: Opening name/id (e.g., 'D1', 'W2')
            room_names: List of room names to assign to
            mode: 'add' to add to existing, 'set' to make the provided list the only assignments

        Returns:
            Number of rooms updated
        """
        updated = 0
        if not opening_id or not room_names:
            return 0

        # Ensure uniqueness
        target_set = set(room_names)

        # Update room.opening_ids
        for room in self.rooms:
            # Determine whether this room should contain the opening
            room_name = getattr(room, 'name', None) if not isinstance(room, dict) else room.get('name')
            should_have = room_name in target_set

            # Current list
            ids = self.get_room_opening_ids(room) or []

            if mode == 'set':
                # In set mode: include opening if room in target_set, remove otherwise
                had = opening_id in ids
                if should_have and not had:
                    ids.append(opening_id)
                    self.set_room_opening_ids(room, ids)
                    updated += 1
                elif not should_have and had:
                    ids = [oid for oid in ids if oid != opening_id]
                    self.set_room_opening_ids(room, ids)
                    updated += 1
            else:  # add mode
                if should_have and opening_id not in ids:
                    ids.append(opening_id)
                    self.set_room_opening_ids(room, ids)
                    updated += 1

        # Also update opening.assigned_rooms if present
        opening = self.get_opening_by_id(opening_id)
        if opening is not None:
            if isinstance(opening, dict):
                assigned = opening.get('assigned_rooms') or []
                if mode == 'set':
                    opening['assigned_rooms'] = list(target_set)
                else:
                    opening['assigned_rooms'] = list(set(assigned) | target_set)
            else:
                assigned = getattr(opening, 'assigned_rooms', []) or []
                if mode == 'set':
                    setattr(opening, 'assigned_rooms', list(target_set))
                else:
                    setattr(opening, 'assigned_rooms', list(set(assigned) | target_set))

        return updated
