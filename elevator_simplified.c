#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

#define MAX_FLOORS 100

typedef enum {
    IDLE,
    MOVING_UP,
    MOVING_DOWN
} ElevatorState;

typedef struct {
    int current_floor;
    ElevatorState state;
    bool up_requests[MAX_FLOORS];
    bool down_requests[MAX_FLOORS];
    int total_floors;
} Elevator;

int main() {
    Elevator elevator;
    int total_floors = 10;
    int i, next_floor, step = 1;

    elevator.current_floor = 1;
    elevator.state = IDLE;
    elevator.total_floors = total_floors;
    for (i = 0; i < MAX_FLOORS; i++) {
        elevator.up_requests[i] = false;
        elevator.down_requests[i] = false;
    }

    printf("Elevator initialized with %d floors\n", total_floors);
    printf("\n=== Elevator Status ===\n");
    printf("Current Floor: %d\n", elevator.current_floor);
    printf("State: IDLE\n");
    printf("=======================\n\n");

    elevator.up_requests[5] = true;
    printf("Added up request for floor 5\n");
    elevator.down_requests[3] = true;
    printf("Added down request for floor 3\n");
    elevator.up_requests[7] = true;
    printf("Added up request for floor 7\n");
    elevator.down_requests[2] = true;
    printf("Added down request for floor 2\n");
    elevator.up_requests[8] = true;
    printf("Added up request for floor 8\n");
    elevator.down_requests[1] = true;
    printf("Added down request for floor 1\n");

    printf("\n=== Elevator Status ===\n");
    printf("Current Floor: %d\n", elevator.current_floor);
    printf("State: IDLE\n");
    printf("Up Requests: ");
    for (i = 1; i <= total_floors; i++) {
        if (elevator.up_requests[i]) printf("%d ", i);
    }
    printf("\nDown Requests: ");
    for (i = 1; i <= total_floors; i++) {
        if (elevator.down_requests[i]) printf("%d ", i);
    }
    printf("\n=======================\n\n");

    while (true) {
        bool has_requests = false;
        for (i = 1; i <= total_floors; i++) {
            if (elevator.up_requests[i] || elevator.down_requests[i]) {
                has_requests = true;
                break;
            }
        }
        if (!has_requests) break;

        printf("--- Step %d ---\n", step++);

        next_floor = -1;
        if (elevator.state == MOVING_UP) {
            for (i = elevator.current_floor + 1; i <= total_floors; i++) {
                if (elevator.up_requests[i]) {
                    next_floor = i;
                    break;
                }
            }
            if (next_floor == -1) {
                for (i = total_floors; i >= 1; i--) {
                    if (elevator.down_requests[i]) {
                        next_floor = i;
                        break;
                    }
                }
            }
        } else if (elevator.state == MOVING_DOWN) {
            for (i = elevator.current_floor - 1; i >= 1; i--) {
                if (elevator.down_requests[i]) {
                    next_floor = i;
                    break;
                }
            }
            if (next_floor == -1) {
                for (i = 1; i <= total_floors; i++) {
                    if (elevator.up_requests[i]) {
                        next_floor = i;
                        break;
                    }
                }
            }
        }

        if (next_floor == -1) {
            int up_dist = total_floors + 1, down_dist = total_floors + 1;
            int up_floor = -1, down_floor = -1;

            for (i = 1; i <= total_floors; i++) {
                if (elevator.up_requests[i]) {
                    int dist = abs(i - elevator.current_floor);
                    if (dist < up_dist) {
                        up_dist = dist;
                        up_floor = i;
                    }
                }
                if (elevator.down_requests[i]) {
                    int dist = abs(i - elevator.current_floor);
                    if (dist < down_dist) {
                        down_dist = dist;
                        down_floor = i;
                    }
                }
            }

            if (up_floor != -1 && down_floor != -1) {
                next_floor = (up_dist <= down_dist) ? up_floor : down_floor;
            } else if (up_floor != -1) {
                next_floor = up_floor;
            } else {
                next_floor = down_floor;
            }
        }

        if (next_floor > elevator.current_floor) {
            elevator.state = MOVING_UP;
            elevator.current_floor++;
            printf("Elevator moving up to floor %d\n", elevator.current_floor);
        } else if (next_floor < elevator.current_floor) {
            elevator.state = MOVING_DOWN;
            elevator.current_floor--;
            printf("Elevator moving down to floor %d\n", elevator.current_floor);
        }

        bool served = false;
        if (elevator.up_requests[elevator.current_floor]) {
            elevator.up_requests[elevator.current_floor] = false;
            printf("Served up request at floor %d\n", elevator.current_floor);
            served = true;
        }
        if (elevator.down_requests[elevator.current_floor]) {
            elevator.down_requests[elevator.current_floor] = false;
            printf("Served down request at floor %d\n", elevator.current_floor);
            served = true;
        }
        if (served) {
            printf("Doors opening at floor %d...\n", elevator.current_floor);
            printf("Doors closing at floor %d...\n", elevator.current_floor);
        }
    }

    printf("\nAll requests processed!\n");
    printf("\n=== Elevator Status ===\n");
    printf("Current Floor: %d\n", elevator.current_floor);
    printf("State: ");
    switch (elevator.state) {
        case IDLE: printf("IDLE\n"); break;
        case MOVING_UP: printf("MOVING UP\n"); break;
        case MOVING_DOWN: printf("MOVING DOWN\n"); break;
    }
    printf("=======================\n\n");

    return 0;
}
