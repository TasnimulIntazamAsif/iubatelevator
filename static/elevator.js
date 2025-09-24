const ALL_FLOORS = [0,1,2,3,4,5,6,7,8,9,10,11,12,13];
const FLOOR_LABELS = {0: "Ground Floor", 1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9", 10: "10", 11: "11", 12: "12", 13: "13"};

document.addEventListener('DOMContentLoaded', function () {
  const selectElevator = document.getElementById('selectElevator');
  const buttonPanel = document.getElementById('buttonPanel');
  const elevatorCar = document.getElementById('elevatorCar');
  const elevatorShaft = document.getElementById('elevatorShaft');
  const doorStatus = document.getElementById('doorStatus');
  const stateLog = document.getElementById('stateLog');

  let currentElevator = selectElevator.value;
  let currentFloor = 0;

  function createButtons() {
    buttonPanel.innerHTML = '';
    ALL_FLOORS.forEach(floor => {
      let btn = document.createElement('button');
      btn.classList.add('floor-button');
      btn.textContent = FLOOR_LABELS[floor];
      btn.dataset.floor = floor;
      btn.onclick = () => pressButton(floor, btn);
      buttonPanel.appendChild(btn);
    });
  }

  function markButtons(validFloors) {
    Array.from(buttonPanel.children).forEach(b => {
      let f = parseInt(b.dataset.floor);
      b.classList.remove('disabled', 'invalid', 'valid');
      b.style.backgroundColor = '';
      // Don't mark invalid buttons with any special styling
      // if (!validFloors.includes(f)) {
      //   b.classList.add('invalid');
      // }
    });
  }

  function pressButton(floor, btn) {
    fetch('/press_button', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ elevator_id: currentElevator, floor: floor })
    }).then(res => res.json())
      .then(data => {
        if (data.success) {
          btn.style.backgroundColor = 'green';
        } else {
          btn.style.backgroundColor = 'red';
          setTimeout(() => btn.style.backgroundColor = '', 2000);
        }
        fetchStatus();
      });
  }

  selectElevator.addEventListener('change', () => {
    currentElevator = selectElevator.value;
    createButtons();
    // Mark buttons for current elevator type
    fetch(`/get_status?elevator_id=${currentElevator}`)
      .then(res => res.json())
      .then(data => {
        let validFloors;
        if (data.queue && data.queue.length) {
          validFloors = ALL_FLOORS;
        } else {
          // Get elevator type from the select option text
          const elevatorType = selectElevator.options[selectElevator.selectedIndex].text.includes('odd') ? 'odd' : 'even';
          validFloors = elevatorType === 'even' ? [0,2,4,6,8,10,12] : [0,1,3,5,7,9,11,13];
        }
        // Or get from backend: validFloors = elevators[currentElevator].floors;
        // Here for simplicity we derive from even/odd logic
        markButtons(validFloors);
      });
    fetchStatus();
  });

  function updateElevatorPosition(floor, doorOpen) {
    // 14 possible positions for floors 0-13
    elevatorCar.style.bottom = (floor * 30) + 'px';
    currentFloor = floor;
    doorStatus.textContent = doorOpen ? 'Door Open' : 'Door Closed';
  }

  function fetchStatus() {
    fetch(`/get_status?elevator_id=${currentElevator}`)
      .then(res => res.json())
      .then(data => {
        if (data.error) {
          alert(data.error);
          return;
        }
        updateElevatorPosition(data.current_floor, data.door_open);
        // Reset buttons if door closed
        if (!data.door_open) {
          Array.from(buttonPanel.children).forEach(b => b.style.backgroundColor = '');
        }
        // Enhanced DFA Trace
        stateLog.value = '';
        if (data.log) {
          data.log.forEach(msg => stateLog.value += msg + '\n');
        }
        if(data.dfa_trace) {
          stateLog.value += data.dfa_trace + '\n';
        }
        stateLog.scrollTop = stateLog.scrollHeight;
      });
  }

  createButtons();
  fetchStatus();
  setInterval(fetchStatus, 2000);
});
