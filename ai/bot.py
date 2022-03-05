from sdk import *
import sys
from time import time

# Reading my team id from the command line args
team_id = int(sys.argv[1])
def game_loop(game_state: GameState, game_time: int, log: Logger) -> PlayerOrder:
    now = time()
    # log.info(f"Received the game state. My team is {team_id}")

    my_cars = [car for car in game_state.cars if car.team_id == team_id]
    if game_state.is_started:
        # The game has started. Deciding what to do with our two ships
        def order_for_car(car: Car) -> PlayerOrder:
            # Here we decided to apply the same rule for our two ships
            if not car.boost_used:
                # The boost is still free to use, let's use it!
                return UseBoost(car.id, team_id)
            # The boost has already been used. We decide to move towards the next checkpoint (planet)
            next_checkpoint = car.next_checkpoint(game_state)
            # The following is morally equivalent to
            # ApplyForce(car.id, team_id, [argument of next_checkpoint.pos - car.pos], 100)
            # (tip: that argument can be computed with atan2)
            return ForceTowards(car.id, team_id, next_checkpoint.pos, 50)

        def attacking_car(car: Car) -> PlayerOrder:
            lightest_car = game_state.get_lightest_car(1 - team_id)
            next_checkpoint = lightest_car.next_checkpoint(game_state)
            next_next_checkpoint = lightest_car.next_next_checkpoint(game_state)

            if game_state.distance(car.pos, next_checkpoint.pos) < 30 and game_state.distance(lightest_car.pos, next_checkpoint.pos) > 100:
                next_next_checkpoint = next_checkpoint
                log.info("waiting him to come")
            
            if game_state.distance(lightest_car.pos, car.pos) < 200 and next_next_checkpoint.checkpoint_index == next_checkpoint.checkpoint_index :
                log.info("going to confront the ship")
                return ForceTowards(car.id, team_id, lightest_car.pos, 100)
            
            #log.info(f"lightest car is {lightest_car.mass}")
            #log.info(f"pos of next checkpoint {next_next_checkpoint.pos}")
            if game_state.distance(car.pos, next_next_checkpoint.pos) < 30 and abs(car.speed) > 30:
                return ForceTowards(car.id, team_id, car.get_braking_point_2(next_next_checkpoint, game_state), 100)
            return ForceTowards(car.id, team_id, next_next_checkpoint.pos, 100)
            
        def running_car(car: Car) -> PlayerOrder:
            next_checkpoint = car.next_checkpoint(game_state)
            if not car.boost_used and len(car.passed_checkpoints) >3:
                return UseBoost(car.id, team_id)
            if 50 <= car.distance_to_next_checkpoint(game_state) < 150 and abs(car.speed) > 200:
                return ForceTowards(car.id, team_id, car.get_braking_point(game_state), 100)
            if car.distance_to_next_checkpoint(game_state) < 50 and abs(car.speed) > 100:
                return ForceTowards(car.id, team_id, car.get_braking_point(game_state), 100)
            return ForceTowards(car.id, team_id, next_checkpoint.pos, 100)


        # log.info("I'm creating my order")
        order = OrderForEachCar(running_car(my_cars[0]), attacking_car(my_cars[1]))

    else:
        # Game has not yet started. It is the only place where we can (and must!) set the masses for the ships.
        order = SetCarMasses(team_id, my_cars[0].id, my_cars[1].id, 5, 15)

    time_taken = time() - now
    # Logging how much time it took.
    # log.info(f"It took {time_taken * 1000000} micro seconds to complete.")
    return order

# Starting the game loop, you can leave this line as is.
Runner(team_id, game_loop).run()