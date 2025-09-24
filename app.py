from flask import Flask, render_template, request, jsonify
from threading import Timer

app = Flask(__name__)

# Elevator data
elevators = {
    'E1': {'floors': 'even', 'current_floor': 0, 'door_open': False, 'queue': [], 'moving': False, 'direction': None},
    'E2': {'floors': 'even', 'current_floor': 0, 'door_open': False, 'queue': [], 'moving': False, 'direction': None},
    'E3': {'floors': 'odd', 'current_floor': 0, 'door_open': False, 'queue': [], 'moving': False, 'direction': None},
    'E4': {'floors': 'odd', 'current_floor': 0, 'door_open': False, 'queue': [], 'moving': False, 'direction': None}
}

valid_floors = {
    'even': [0, 2, 4, 6, 8, 10, 12],
    'odd': [0, 1, 3, 5, 7, 9, 11, 13]
}

state_logs = {eid: [] for eid in elevators.keys()}
dfa_traces = {eid: None for eid in elevators.keys()}

def log_state(eid, msg):
    """Logs state transitions for a specific elevator.
    
    Args:
        eid: Elevator ID
        msg: Message to log
        
    Maintains a rolling log of the last 20 state transitions.
    """
    logs = state_logs[eid]
    logs.append(msg)
    if len(logs) > 20:
        logs.pop(0)

def dfa_path_trace(eid, start, end):
    """Generates a DFA (Deterministic Finite Automaton) path trace between floors.
    
    Args:
        eid: Elevator ID
        start: Starting floor number
        end: Destination floor number
        
    Returns:
        String representation of the DFA path trace (e.g., "q0>q2>q4")
        
    This function models the elevator movement as a state machine transition,
    where each floor is a state (q0, q1, q2, etc.) and the path shows transitions
    between states.
    """
    floors = valid_floors[elevators[eid]['floors']]
    elevator_type = elevators[eid]['floors']
    
    # Special case for moving between ground floor and first floor for odd elevators
    if elevator_type == 'odd' and ((start == 0 and end == 1) or (start == 1 and end == 0)):
        step = 1
    else:
        step = 2
        
    if start == end:
        return f"q{start}"
    path = [f"q{start}"]
    current = start
    if end > start:
        while current < end:
            current += step
            path.append(f"q{current}")
    else:
        while current > end:
            current -= step
            path.append(f"q{current}")
    return ">".join(path)

def move_one_floor(eid):
    """Moves an elevator one step toward its next destination.
    
    Args:
        eid: Elevator ID
        
    This function handles the elevator movement logic, including:
    - Stopping when the queue is empty
    - Opening doors when arriving at a destination
    - Moving up or down based on the target floor
    - Special handling for odd elevators moving between ground floor and first floor
    - Generating DFA traces for state transitions
    """
    elevator = elevators[eid]
    if not elevator['queue']:
        elevator['moving'] = False
        elevator['direction'] = None
        return

    target = elevator['queue'][0]
    current = elevator['current_floor']

    if current == target:
        elevator['door_open'] = True
        elevator['moving'] = False
        elevator['direction'] = None
        log_state(eid, f"Arrived at floor {target}.")
        log_state(eid, dfa_path_trace(eid, current, target))
        dfa_traces[eid] = None  # Clear DFA trace on arrival (door opening)
        Timer(5, close_door, [eid]).start()
        elevator['queue'].pop(0)
        return

    elevator['moving'] = True
    prev_floor = elevator['current_floor']
    elevator_type = elevator['floors']
    
    # Special case for moving between ground floor and first floor for odd elevators
    if elevator_type == 'odd' and ((current == 0 and target >= 1) or (current == 1 and target == 0)):
        if target > current:
            elevator['current_floor'] = 1
            elevator['direction'] = 'up'
            log_state(eid, f"Moving up to floor {elevator['current_floor']}.")
        else:
            elevator['current_floor'] = 0
            elevator['direction'] = 'down'
            log_state(eid, f"Moving down to floor {elevator['current_floor']}.")
    else:
        # Normal case - move by 2 floors
        if target > current:
            elevator['current_floor'] += 2
            elevator['direction'] = 'up'
            log_state(eid, f"Moving up to floor {elevator['current_floor']}.")
        else:
            elevator['current_floor'] -= 2
            elevator['direction'] = 'down'
            log_state(eid, f"Moving down to floor {elevator['current_floor']}.")
    trace = dfa_path_trace(eid, prev_floor, elevator['current_floor'])
    log_state(eid, trace)
    dfa_traces[eid] = trace
    Timer(2, move_one_floor, [eid]).start()

def close_door(eid):
    """Closes the elevator door after a delay.
    
    Args:
        eid: Elevator ID
        
    This function is called by a Timer to close the door after the elevator
    has arrived at a destination. If there are more floors in the queue,
    it will continue moving to the next destination.
    """
    elevator = elevators[eid]
    elevator['door_open'] = False
    log_state(eid, f"Door closed at floor {elevator['current_floor']}. Waiting for input.")
    # Do not add DFA trace after door close
    dfa_traces[eid] = None
    if elevator['queue']:
        move_one_floor(eid)

@app.route('/')
def index():
    """Renders the main elevator control interface.
    
    Returns:
        Rendered HTML template with elevator data and valid floor information.
    """
    return render_template('index.html', elevators=elevators, valid_floors=valid_floors)

@app.route('/validate_button', methods=['POST'])
def validate_button():
    """API endpoint to validate if a floor button is valid for a specific elevator.
    
    Request JSON parameters:
        elevator_id: ID of the elevator
        floor: Floor number to validate
        
    Returns:
        JSON response with 'valid' boolean indicating if the floor is valid
        for the specified elevator.
    """
    data = request.json
    eid = data['elevator_id']
    floor = int(data['floor'])
    elevator = elevators[eid]
    valid = floor in valid_floors[elevator['floors']]
    return jsonify({'valid': valid})

@app.route('/press_button', methods=['POST'])
def press_button():
    """API endpoint to request an elevator to a specific floor.
    
    Request JSON parameters:
        elevator_id: ID of the elevator
        floor: Floor number to request
        
    Returns:
        JSON response with:
        - 'success': Boolean indicating if the request was successful
        - 'message': Error message if request failed
        
    This function adds the requested floor to the elevator's queue and
    initiates movement if the elevator is idle.
    """
    data = request.json
    eid = data['elevator_id']
    floor = int(data['floor'])
    elevator = elevators[eid]

    if floor not in valid_floors[elevator['floors']]:
        return jsonify({'success': False, 'message': 'Invalid floor for this elevator.'})

    if floor in elevator['queue'] or floor == elevator['current_floor']:
        return jsonify({'success': False, 'message': 'Floor already requested or current floor.'})

    elevator['queue'].append(floor)
    log_state(eid, f"Floor {floor} requested.")
    if not elevator['moving'] and not elevator['door_open']:
        move_one_floor(eid)
    return jsonify({'success': True})

@app.route('/get_status')
def get_status():
    """API endpoint to get the current status of an elevator.
    
    Query parameters:
        elevator_id: ID of the elevator
        
    Returns:
        JSON response with elevator status information including:
        - current_floor: Current floor number
        - door_open: Boolean indicating if door is open
        - moving: Boolean indicating if elevator is moving
        - direction: Movement direction ('up', 'down', or null)
        - queue: List of requested floors
        - log: List of state transition messages
        - dfa_trace: Current DFA path trace (if any)
    """
    eid = request.args.get('elevator_id')
    if eid not in elevators:
        return jsonify({'error': 'Invalid elevator id'})
    elevator = elevators[eid]
    return jsonify({
        'current_floor': elevator['current_floor'],
        'door_open': elevator['door_open'],
        'moving': elevator['moving'],
        'direction': elevator['direction'],
        'queue': elevator['queue'],
        'log': state_logs[eid],
        'dfa_trace': dfa_traces[eid] or ""
    })

if __name__ == '__main__':
    app.run(debug=True)
