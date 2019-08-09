
import battlecode as bc;

class Helper:
	def get_opposing_team(t): #Team => Team
		if (t == bc.Team.Red):
			return bc.Team.Blue;
		else:
			return bc.Team.Red;

	def get_other_planet(p): #Planet => Planet
		if (p == bc.Planet.Earth):
			return bc.Planet.Mars;
		else:
			return bc.Planet.Earth;

	def get_inverse(dir): #Direction => Direction
		if (dir is None):
			return None;
		if dir == bc.Direction.East:
			return bc.Direction.West;
		elif dir == bc.Direction.North:
			return bc.Direction.South;
		elif dir == bc.Direction.Northeast:
			return bc.Direction.Southwest;
		elif dir == bc.Direction.Northwest:
			return bc.Direction.Southeast;
		elif dir == bc.Direction.South:
			return bc.Direction.North;
		elif dir == bc.Direction.Southeast:
			return bc.Direction.Northwest;
		elif dir == bc.Direction.Southwest:
			return bc.Direction.Northeast;
		elif dir == bc.Direction.West:
			return bc.Direction.East;
		else:
			return bc.Direction.Center;

	def is_offensive_robot(unit): #Unit => Boolean
		if (unit.unit_type == bc.UnitType.Ranger or unit.unit_type == bc.UnitType.Knight or unit.unit_type == bc.UnitType.Mage):
			return True;
		else:
			return False;