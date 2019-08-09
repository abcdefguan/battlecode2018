
import battlecode as bc
from worker import Worker
from astronomer import Astronomer
from enum import Enum

class Engineer:

	class GamePhase(Enum):
		EARLY_GAME = 1;
		MID_GAME = 2;

	overcrowding_limit = 40;
	min_worker_num = 5;
	early_game_end = 100;
	real_early_game = 50;
	knight_override = False;
	mage_override = False;
	samosa_override = False; #counters samosa strats
	samosa_sense_range = 5;
	directions = [bc.Direction.East, bc.Direction.North, bc.Direction.Northeast,
	bc.Direction.Northwest, bc.Direction.South, bc.Direction.Southeast,
	bc.Direction.Southwest, bc.Direction.West];
	unit_types = [bc.UnitType.Worker, bc.UnitType.Knight, bc.UnitType.Ranger, bc.UnitType.Mage, bc.UnitType.Healer]
	unit_ratio_early_game = [0, 0, 2, 0, 1];
	unit_ratio_mid_game = [0, 0, 2, 0, 1];

	def __init__(self, gc, intel_map, mov, astro): #GameController, IntelMap, Mover, Astronomer
		self.gc = gc;
		self.intel_map = intel_map;
		self.mov = mov;
		self.astro = astro;
		self.worker_assign = {}; #dict int => Worker

	def take_turn(self, workers, factories, unit_cnt): #[Unit], [Unit], [int] => void
		for worker in workers:
			w = self.worker_assign.get(worker.id);
			if (w is None):
				w = Worker(self.gc, self.intel_map, self.mov, self.astro);
				self.worker_assign[worker.id] = w;
			w.take_turn(worker, factories, workers);

		for factory in factories:
			next_unit_type = self.get_built_unit_type(unit_cnt);

			if (not(next_unit_type is None) and factory.structure_is_built() and not(factory.is_factory_producing()) and
			self.gc.karbonite() >= next_unit_type.factory_cost() ):
				if (self.gc.can_produce_robot(factory.id, next_unit_type)):
					self.gc.produce_robot(factory.id, next_unit_type);
			if (len(factory.structure_garrison()) > 0):
				cannot_unload = True;
				for direc in Engineer.directions:
					if (self.gc.can_unload(factory.id, direc)):
						self.gc.unload(factory.id, direc);
						cannot_unload = False;
				if (cannot_unload):
					nearby_workers = self.gc.sense_nearby_units_by_type(factory.location.map_location(), Engineer.samosa_sense_range, bc.UnitType.Worker);
					if (not(Engineer.samosa_override)):
						for worker in nearby_workers:
							if (worker.team != self.gc.team()):
								Engineer.samosa_override = True;
								break;
					if (Engineer.samosa_override):
						for direc in Engineer.directions:
							new_loc = factory.location.map_location().add(direc);
							if (self.gc.can_sense_location(new_loc) and self.gc.has_unit_at_location(new_loc)):
								unit = self.gc.sense_unit_at_location(new_loc);
								if (unit.team == self.gc.team() and unit.unit_type == bc.UnitType.Worker):
									self.gc.disintegrate_unit(unit.id);
									if (self.gc.can_unload(factory.id, direc)):
										self.gc.unload(factory.id, direc);
										break;



	def get_built_unit_type(self, unit_cnt): #int[] => UnitType
		if (Engineer.samosa_override and self.gc.round() < 75):
			return bc.UnitType.Mage;
		if (unit_cnt[0] < Engineer.min_worker_num and self.gc.round() > 400):
			return bc.UnitType.Worker;
		tot_cnt = 0;
		for i in range(1, len(unit_cnt)):
			tot_cnt += unit_cnt[i];
		if (tot_cnt >= Engineer.overcrowding_limit):
			return None;
		if (self.gc.round() >= Astronomer.rocket_panic_round):
			return None;
		ratio_cnt = 0;
		if (self.get_game_phase() == Engineer.GamePhase.EARLY_GAME):
			for i in range(len(Engineer.unit_ratio_early_game)):
				ratio_cnt += Engineer.unit_ratio_early_game[i];
		elif (self.get_game_phase() == Engineer.GamePhase.MID_GAME):
			for i in range(len(Engineer.unit_ratio_mid_game)):
				ratio_cnt += Engineer.unit_ratio_mid_game[i];

		expected_no = [0, 0, 0, 0, 0];
		if (self.get_game_phase() == Engineer.GamePhase.EARLY_GAME):
			for i in range(5):
				expected_no[i] = (Engineer.unit_ratio_early_game[i] * tot_cnt + ratio_cnt - 1) // ratio_cnt;
		elif (self.get_game_phase() == Engineer.GamePhase.MID_GAME):
			for i in range(5):
				expected_no[i] = (Engineer.unit_ratio_mid_game[i] * tot_cnt + ratio_cnt - 1) // ratio_cnt;
		for i in range(4, -1, -1):
			if (expected_no[i] > unit_cnt[i]):
				return Engineer.unit_types[i];
		#print("Unit Types unexpectedly meet ratio: Defaulting to Ranger");
		if (Engineer.mage_override and self.gc.round() < Engineer.early_game_end):
			return bc.UnitType.Mage;
		elif (Engineer.knight_override and self.gc.round() < Engineer.early_game_end):
			return bc.UnitType.Knight;
		return bc.UnitType.Healer;

	def get_game_phase(self): # => GamePhase
		if (self.gc.round() > Engineer.early_game_end):
			return Engineer.GamePhase.MID_GAME;
		else:
			return Engineer.GamePhase.EARLY_GAME;