
import battlecode as bc

class Researcher:
	def __init__(self, gc, intel_map):
		self.gc = gc;
		self.intel_map = intel_map;

		gc.queue_research(bc.UnitType.Worker);
		gc.queue_research(bc.UnitType.Healer);
		gc.queue_research(bc.UnitType.Healer);
		gc.queue_research(bc.UnitType.Rocket);
		gc.queue_research(bc.UnitType.Healer);
		gc.queue_research(bc.UnitType.Ranger);
		gc.queue_research(bc.UnitType.Ranger);
		gc.queue_research(bc.UnitType.Ranger);
		gc.queue_research(bc.UnitType.Rocket);
		gc.queue_research(bc.UnitType.Rocket);

	def take_turn(self):
		0
		#Do nothing for now, will do shtuff later