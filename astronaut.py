import battlecode as bc
from enum import Enum

class Astronaut:
	rocket_panic_round = 550;
	forced_launch_round = 746;
	emergency_liftoff_health = 150; #Min amt of health to force a liftOff
	max_wait_time = 50; #Maximum number of rounds to wait to be loaded
	directions = [bc.Direction.East, bc.Direction.North, bc.Direction.Northeast,
	bc.Direction.Northwest, bc.Direction.South, bc.Direction.Southeast,
	bc.Direction.Southwest, bc.Direction.West];

	class MissionType(Enum):
		Resourcing = 1
		Salvation = 2

	def __init__(self, gc, intel_map, astro, unit):
		self.gc = gc;
		self.intel_map = intel_map;
		self.astro = astro;
		self.unit = unit;
		self.mission_type = None;
		self.has_landed = False;
		self.start_round = -1;
		self.mission_type = Astronaut.MissionType.Salvation;
		self.is_requesting_crew = True;

	def take_turn(self, unit): # Unit => None
		if (self.start_round == -1):
			self.start_round = self.gc.round();

		self.unit = unit

		if not(self.unit.structure_is_built()):
			return;

		if not(self.unit.rocket_is_used()):
			#Load units of the particular type that I want
			nearby_allied_units = self.gc.sense_nearby_units_by_team(self.unit.location.map_location(), 3, self.gc.team());
			num_loaded_units = len(self.unit.structure_garrison());
			for ally in nearby_allied_units:
				if (num_loaded_units == self.unit.structure_max_capacity()):
					break;
				if (self.mission_type == Astronaut.MissionType.Salvation):
					can_load_unit = False;
					if (num_loaded_units < 4 and self.gc.round() < Astronaut.rocket_panic_round):
						if (ally.unit_type != bc.UnitType.Rocket and ally.unit_type != bc.UnitType.Factory):
							can_load_unit = True;
					else:
						if (ally.unit_type != bc.UnitType.Rocket and ally.unit_type != bc.UnitType.Factory and ally.unit_type != bc.UnitType.Worker):
							can_load_unit = True;
					if (can_load_unit):
						#Attempt to load ally
						if (self.gc.can_load(unit.id, ally.id)):
							self.gc.load(self.unit.id, ally.id);
							num_loaded_units += 1;
			#Reacquire unit
			if self.gc.can_sense_unit(self.unit.id):
				self.unit = self.gc.unit(self.unit.id)
			#Launch rocket if taking too much damage
			if self.unit.health <= Astronaut.emergency_liftoff_health:
				self.lift_off();
				return;
			#Launch rocket if it's full
			if num_loaded_units == self.unit.structure_max_capacity():
				self.lift_off();
				return;
			#Launch rocket if it's too late
			if self.gc.round() >= Astronaut.forced_launch_round:
				self.lift_off();
				return;
			#Launch rocket if it's waited too long
			if self.gc.round() - self.start_round >= Astronaut.max_wait_time:
				self.lift_off();
				return;
		else:
			if not(self.has_landed):
				#print("The eagle has landed");
				self.has_landed = True;
			garrison_len = len(self.unit.structure_garrison())
			while garrison_len > 0:
				for direc in Astronaut.directions:
					if (self.gc.can_unload(self.unit.id, direc)):
						self.gc.unload(self.unit.id, direc)
						garrison_len -= 1;
						continue;
				break;

	def lift_off(self): #void => void
		landing_site = None;
		if self.mission_type == Astronaut.MissionType.Salvation:
			landing_site = self.astro.get_salvation_rocket_land_location();
		if landing_site is None:
			print("Abort abort... We can't find a landing site (This shouldn't happen)");
			return;
		print("Recommended landing site at: (" + str(landing_site.x) + " , " + str(landing_site.y) + ")");
		if self.gc.can_launch_rocket(self.unit.id, landing_site):
			self.gc.launch_rocket(self.unit.id, landing_site);
			self.astro.launch_rocket(landing_site);
			#print("And we have achieved... Liftoff");
		else:
			print("Abort abort... We can't actually launch (This shouldn't happen)");

	def is_requesting_unit_type(self, unit_type): #UnitType => boolean
		if self.mission_type == Astronaut.MissionType.Salvation:
			if unit_type != bc.UnitType.Rocket and unit_type != bc.UnitType.Factory:
				return True;
			else:
				return False;
		return False;