# IUBAT Elevator Simulator

Interactive multi-elevator controller built with Flask, vanilla JS, and CSS. The app simulates four elevators in IUBAT's campus, splitting traffic across even/odd floor pairs and visualizing DFA-style state transitions as the cars move.

## Features
- Web UI (`templates/index.html`) with floor buttons, shaft visualization, and rolling state log.
- Four virtual elevators (`app.py`) with distinct floor access rules, movement queues, and door timing handled via Python `Timer`.
- DFA path traces for every move, showing state transitions between floors.
- REST-style endpoints (`/press_button`, `/get_status`, `/validate_button`) consumed by the frontend (`static/elevator.js`) for live updates every two seconds.

## Project Structure
- `app.py` – Flask server, elevator state machine, HTTP endpoints.
- `templates/index.html` – Control panel UI.
- `static/elevator.js` – Frontend logic (button handling, polling, visualization).
- `static/elevator.css` – Styling for the control panel and shaft.
- `LICENSE` – Project license.

## Getting Started

### Prerequisites
- Python 3.9+ (virtualenv recommended)

### Installation
```bash
python -m venv .venv
.venv\Scripts\activate  # or source .venv/bin/activate on Unix
pip install flask
```

### Run
```bash
set FLASK_APP=app.py       # export FLASK_APP=app.py on Unix
flask run --debug
```
Visit http://127.0.0.1:5000 and interact with the control panel.

## API Overview
- `POST /press_button` – enqueue a floor request for an elevator ID (`E1`-`E4`).
- `POST /validate_button` – check whether a floor is reachable by a given elevator.
- `GET /get_status?elevator_id=E1` – retrieve current floor, door/motion status, queue, and latest DFA trace.

## Frontend Behavior
The JS client renders all floors, colors buttons green/red based on request success, polls the backend every two seconds, and rewrites the state log textarea so you can observe move-by-move DFA traces.

## Testing Ideas
- Use curl or Postman to call `/press_button` with various floor combos and ensure even/odd validation works.
- Rapidly enqueue multiple floors for a single elevator to verify queuing and log rotation.

## Future Improvements
- Persist logs/state across restarts.
- Add automated tests for queue ordering and DFA traces.
- Replace polling with WebSockets for smoother updates.

