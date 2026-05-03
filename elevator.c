#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>

#define MAX_FLOORS 100
#define MAX_REQUESTS 1000

typedef enum {
    IDLE,
    MOVING_UP,
    MOVING_DOWN,
    DOOR_OPENING,
    DOOR_CLOSING
} ElevatorState;

typedef struct {
    int floor;
    bool is_up;
    bool is_internal;
} Request;

typedef struct {
    int current_floor;
    ElevatorState state;
    int up_requests[MAX_FLOORS];
    int down_requests[MAX_FLOORS];
    int up_count;
    int down_count;
    int total_floors;
} Elevator;

void elevator_init(Elevator *elevator, int total_floors) {
    elevator->current_floor = 1;
    elevator->state = IDLE;
    elevator->total_floors = total_floors;
    elevator->up_count = 0;
    elevator->down_count = 0;
    memset(elevator->up_requests, 0, sizeof(elevator->up_requests));
    memset(elevator->down_requests, 0, sizeof(elevator->down_requests));
}

int binary_search_insert(int *arr, int count, int value, bool ascending) {
    int left = 0;
    int right = count - 1;
    int insert_pos = count;

    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (ascending) {
            if (arr[mid] < value) {
                left = mid + 1;
            } else {
                insert_pos = mid;
                right = mid - 1;
            }
        } else {
            if (arr[mid] > value) {
                left = mid + 1;
            } else {
                insert_pos = mid;
                right = mid - 1;
            }
        }
    }

    if (insert_pos < count) {
        memmove(&arr[insert_pos + 1], &arr[insert_pos], (count - insert_pos) * sizeof(int));
    }
    arr[insert_pos] = value;
    return insert_pos;
}

bool binary_search_exists(int *arr, int count, int value) {
    int left = 0;
    int right = count - 1;

    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (arr[mid] == value) {
            return true;
        } else if (arr[mid] < value) {
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }
    return false;
}

int binary_search_remove(int *arr, int count, int value) {
    int left = 0;
    int right = count - 1;
    int pos = -1;

    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (arr[mid] == value) {
            pos = mid;
            break;
        } else if (arr[mid] < value) {
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }

    if (pos != -1 && pos < count - 1) {
        memmove(&arr[pos], &arr[pos + 1], (count - pos - 1) * sizeof(int));
    }
    return (pos != -1) ? count - 1 : count;
}

void add_request(Elevator *elevator, int floor, bool is_up) {
    if (floor < 1 || floor > elevator->total_floors) {
        printf("Invalid floor: %d\n", floor);
        return;
    }

    if (floor == elevator->current_floor) {
        printf("Already at floor %d, opening doors\n", floor);
        return;
    }

    if (is_up) {
        if (!binary_search_exists(elevator->up_requests, elevator->up_count, floor)) {
            binary_search_insert(elevator->up_requests, elevator->up_count, floor, true);
            elevator->up_count++;
            printf("Added up request for floor %d\n", floor);
        }
    } else {
        if (!binary_search_exists(elevator->down_requests, elevator->down_count, floor)) {
            binary_search_insert(elevator->down_requests, elevator->down_count, floor, false);
            elevator->down_count++;
            printf("Added down request for floor %d\n", floor);
        }
    }
}

int get_next_floor(Elevator *elevator) {
    if (elevator->up_count == 0 && elevator->down_count == 0) {
        return -1;
    }

    if (elevator->state == MOVING_UP) {
        for (int i = 0; i < elevator->up_count; i++) {
            if (elevator->up_requests[i] > elevator->current_floor) {
                return elevator->up_requests[i];
            }
        }
        if (elevator->down_count > 0) {
            return elevator->down_requests[0];
        }
    } else if (elevator->state == MOVING_DOWN) {
        for (int i = 0; i < elevator->down_count; i++) {
            if (elevator->down_requests[i] < elevator->current_floor) {
                return elevator->down_requests[i];
            }
        }
        if (elevator->up_count > 0) {
            return elevator->up_requests[elevator->up_count - 1];
        }
    }

    if (elevator->up_count > 0 && elevator->down_count > 0) {
        int up_distance = abs(elevator->up_requests[0] - elevator->current_floor);
        int down_distance = abs(elevator->down_requests[0] - elevator->current_floor);
        return (up_distance <= down_distance) ? elevator->up_requests[0] : elevator->down_requests[0];
    } else if (elevator->up_count > 0) {
        return elevator->up_requests[0];
    } else {
        return elevator->down_requests[0];
    }
}

void process_current_floor(Elevator *elevator) {
    bool served = false;

    if (binary_search_exists(elevator->up_requests, elevator->up_count, elevator->current_floor)) {
        elevator->up_count = binary_search_remove(elevator->up_requests, elevator->up_count, elevator->current_floor);
        printf("Served up request at floor %d\n", elevator->current_floor);
        served = true;
    }

    if (binary_search_exists(elevator->down_requests, elevator->down_count, elevator->current_floor)) {
        elevator->down_count = binary_search_remove(elevator->down_requests, elevator->down_count, elevator->current_floor);
        printf("Served down request at floor %d\n", elevator->current_floor);
        served = true;
    }

    if (served) {
        printf("Doors opening at floor %d...\n", elevator->current_floor);
        printf("Doors closing at floor %d...\n", elevator->current_floor);
    }
}

void elevator_step(Elevator *elevator) {
    int next_floor = get_next_floor(elevator);

    if (next_floor == -1) {
        elevator->state = IDLE;
        printf("Elevator is idle at floor %d\n", elevator->current_floor);
        return;
    }

    if (next_floor > elevator->current_floor) {
        elevator->state = MOVING_UP;
        elevator->current_floor++;
        printf("Elevator moving up to floor %d\n", elevator->current_floor);
    } else if (next_floor < elevator->current_floor) {
        elevator->state = MOVING_DOWN;
        elevator->current_floor--;
        printf("Elevator moving down to floor %d\n", elevator->current_floor);
    }

    process_current_floor(elevator);
}

bool has_pending_requests(Elevator *elevator) {
    return (elevator->up_count > 0 || elevator->down_count > 0);
}

void print_elevator_status(Elevator *elevator) {
    printf("\n=== Elevator Status ===\n");
    printf("Current Floor: %d\n", elevator->current_floor);
    printf("State: ");
    switch (elevator->state) {
        case IDLE: printf("IDLE\n"); break;
        case MOVING_UP: printf("MOVING UP\n"); break;
        case MOVING_DOWN: printf("MOVING DOWN\n"); break;
        case DOOR_OPENING: printf("DOOR OPENING\n"); break;
        case DOOR_CLOSING: printf("DOOR CLOSING\n"); break;
    }
    printf("Up Requests (%d): ", elevator->up_count);
    for (int i = 0; i < elevator->up_count; i++) {
        printf("%d ", elevator->up_requests[i]);
    }
    printf("\nDown Requests (%d): ", elevator->down_count);
    for (int i = 0; i < elevator->down_count; i++) {
        printf("%d ", elevator->down_requests[i]);
    }
    printf("\n=======================\n\n");
}

int main() {
    Elevator elevator;
    int total_floors = 10;

    elevator_init(&elevator, total_floors);
    printf("Elevator initialized with %d floors\n", total_floors);
    print_elevator_status(&elevator);

    add_request(&elevator, 5, true);
    add_request(&elevator, 3, false);
    add_request(&elevator, 7, true);
    add_request(&elevator, 2, false);
    add_request(&elevator, 8, true);
    add_request(&elevator, 1, false);

    print_elevator_status(&elevator);

    int step = 1;
    while (has_pending_requests(&elevator)) {
        printf("--- Step %d ---\n", step++);
        elevator_step(&elevator);
    }

    printf("\nAll requests processed!\n");
    print_elevator_status(&elevator);

    return 0;
}
