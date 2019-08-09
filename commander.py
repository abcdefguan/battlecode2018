
import battlecode as bc
from helper import Helper
from role import Role
from dice_roller import DiceRoller
from ranger import Ranger
from mage import Mage
from knight import Knight
from soldier import Soldier
from healer import Healer

class Commander:
	scout_role_chance_knight = 0; #Out of 100
	scout_role_chance_ranger = 0; #Out of 100
	all_scout_round = 0; #Round before which everyone is a scout

	def __init__(self, gc, intel_map, mov, astro):
		self.gc = gc;
		self.intel_map = intel_map;
		self.mov = mov;
		self.astro = astro;
		self.rally_point = self.get_default_rally_point();
		self.last_enemy_sighted_loc = None;
		self.on_alert = False;
		self.unit_info = {}; #dict int => Soldier

	def take_turn(self, offensive_units): #[Unit] => void
		all_enemies = self.gc.sense_nearby_units_by_team(bc.MapLocation(self.gc.planet(), 0, 0), 1000000, Helper.get_opposing_team(self.gc.team()));

		if len(all_enemies) > 0:
			self.rally_point = all_enemies[0].location.map_location();
			self.on_alert = True;
		else:
			self.rally_point = self.get_default_rally_point();
			self.on_alert = False;

		for unit in offensive_units:
			soldier = self.unit_info.get(unit.id);
			if soldier is None:
				if unit.unit_type == bc.UnitType.Knight:
					soldier = Knight(self.gc, self.intel_map, self.mov, self.astro, Role.Attack, unit);
				elif unit.unit_type == bc.UnitType.Ranger:
					soldier = Ranger(self.gc, self.intel_map, self.mov, self.astro, Role.Attack, unit);
				elif unit.unit_type == bc.UnitType.Mage:
					soldier = Mage(self.gc, self.intel_map, self.mov, self.astro, Role.Attack, unit);
				elif unit.unit_type == bc.UnitType.Healer:
					soldier = Healer(self.gc, self.intel_map, self.mov, self.astro, Role.Attack, unit, self);
				else:
					soldier = Soldier(self.gc, self.intel_map, self.mov, self.astro, Role.Scout, unit);
			soldier.set_rally_point(self.rally_point);
			self.unit_info[unit.id] = soldier;
			if self.gc.planet() == bc.Planet.Mars:
				soldier.set_role(Role.Scout);
			soldier.set_rally_point(self.rally_point);
			soldier.take_turn(unit, self.on_alert);
			#Carry out soldier move
			soldier.move_and_attack();

	def take_extra_turn(self, unit): # Unit => void
		if (self.gc.can_sense_unit(unit.id)):
			unit = self.gc.unit(unit.id);
		else:
			print("Commander: Can't sense soldier !!");
		#print("Commander: Overcharged unit attack heat is: " + str(unit.attack_heat()));
		soldier = self.unit_info.get(unit.id);
		if soldier is None:
			if unit.unit_type == bc.UnitType.Knight:
				soldier = Knight(self.gc, self.intel_map, self.mov, self.astro, Role.Attack, unit);
			elif unit.unit_type == bc.UnitType.Ranger:
				soldier = Ranger(self.gc, self.intel_map, self.mov, self.astro, Role.Attack, unit);
			elif unit.unit_type == bc.UnitType.Mage:
				soldier = Mage(self.gc, self.intel_map, self.mov, self.astro, Role.Attack, unit);
			elif unit.unit_type == bc.UnitType.Healer:
				soldier = Healer(self.gc, self.intel_map, self.mov, self.astro, Role.Attack, unit, self);
		if not(soldier is None):
			soldier.take_turn(unit, self.on_alert);
			soldier.move_and_attack();

	def get_default_rally_point(self): # => MapLocation
		return self.intel_map.get_default_rally_point(self.gc.planet());