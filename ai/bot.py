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
            most_advanced_car = game_state.get_most_advanced_car(1 - team_id)

            next_checkpoint = most_advanced_car.next_checkpoint(game_state)
            if (game_state.distance(next_checkpoint.pos, most_advanced_car.pos) < game_state.distance(next_checkpoint.pos, car.pos)):
                next_checkpoint = most_advanced_car.next_next_checkpoint(game_state)

            log.info(f"light - car {game_state.distance(most_advanced_car.pos, car.pos)}")
            log.info(f"check - car {game_state.distance(car.pos, next_checkpoint.pos)}")
            if (game_state.distance(most_advanced_car.pos, car.pos) < 200 and game_state.distance(car.pos, next_checkpoint.pos) < 200) or game_state.distance(most_advanced_car.pos, car.pos) < 50:
                log.info("going to confront the ship")
                if game_state.distance(car.pos, most_advanced_car.pos) < 30 and abs(car.speed) > 30:
                    return ForceTowards(car.id, team_id, car.get_braking_point_2(most_advanced_car.pos, game_state), 100)
                return ForceTowards(car.id, team_id, most_advanced_car.pos, 100)
                
            if game_state.distance(car.pos, next_checkpoint.pos) < 30 and abs(car.speed) > 30:
                return ForceTowards(car.id, team_id, car.get_braking_point_2(next_checkpoint, game_state), 100)
            return ForceTowards(car.id, team_id, next_checkpoint.pos, 100)
            
        def running_car(car: Car) -> PlayerOrder:
            next_checkpoint = car.next_checkpoint(game_state).pos
            if not car.boost_used and len(car.passed_checkpoints) > 3:
                return UseBoost(car.id, team_id)
            vit = 100
            if abs(car.speed) > 400:
                vit = 0
            if 50 <= car.distance_to_next_checkpoint(game_state) < 150 and abs(car.speed) > 200:
                return ForceTowards(car.id, team_id, car.get_braking_point(game_state), 100)
            if car.distance_to_next_checkpoint(game_state) < 50 and abs(car.speed) > 100:
                return ForceTowards(car.id, team_id, car.get_braking_point(game_state), 100)
            if car.distance_to_next_checkpoint(game_state) < 50 and 15 < abs(car.speed) < 100:
                return ForceTowards(car.id, team_id, next_checkpoint, 0)
            return ForceTowards(car.id, team_id, next_checkpoint, vit)


        # log.info("I'm creating my order")
        order = OrderForEachCar(running_car(my_cars[0]), attacking_car(my_cars[1]))

    else:
        # Game has not yet started. It is the only place where we can (and must!) set the masses for the ships.
        order = SetCarMasses(team_id, my_cars[0].id, my_cars[1].id, 3, 17)

    time_taken = time() - now
    # Logging how much time it took.
    # log.info(f"It took {time_taken * 1000000} micro seconds to complete.")
    return order

# Starting the game loop, you can leave this line as is.
Runner(team_id, game_loop).run()