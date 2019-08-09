
import battlecode as bc
import random

class DiceRoller:

	def get_random_map_location(planet, planet_width, planet_height): #Planet, int, int => MapLocation
		x = random.randint(0, planet_width - 1);
		y = random.randint(0, planet_height - 1);

		return bc.MapLocation(planet, x, y);

	def percentage_dice_roll(percentage_success): # int => bool
		rand = random.randint(0, 99);
		if (rand < percentage_success):
			return True;
		else:
			return False;

	def get_int(max_int):
		return random.randint(0, max_int - 1);