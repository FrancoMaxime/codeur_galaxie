from sdk import *
import sys
from time import time

# Reading my team id from the command line args
team_id = int(sys.argv[1])

def game_loop(game_state: GameState, game_time: int, log: Logger) -> PlayerOrder:
    now = time()
    log.info(f"Received the game state. My team is {team_id}")

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
            return ForceTowards(car.id, team_id, next_checkpoint.pos, 100)

        def attacking_car(car: Car) -> PlayerOrder:
            lightest_car = GameState.get_lightest_car(1-team_id)
            enemy_location = car.pos
            target_location = car.next_checkpoint().pos
            return ForceTowards(car.id, team_id, target_location, 100)
        log.info("I'm creating my order")
        order = OrderForEachCar(order_for_car(my_cars[0]), order_for_car(my_cars[1]))

    else:
        # Game has not yet started. It is the only place where we can (and must!) set the masses for the ships.
        order = SetCarMasses(team_id, my_cars[0].id, my_cars[1].id, 5, 15)

    time_taken = time() - now
    # Logging how much time it took.
    log.info(f"It took {time_taken * 1000000} micro seconds to complete.")
    return order

# Starting the game loop, you can leave this line as is.
Runner(team_id, game_loop).run()