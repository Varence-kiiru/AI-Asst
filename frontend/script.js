document.addEventListener('DOMContentLoaded', function() {
    // Register form submission
    document.getElementById('registerForm').addEventListener('submit', function(event) {
        event.preventDefault();
        const name = document.getElementById('registerName').value;
        const email = document.getElementById('registerEmail').value;
        const password = document.getElementById('registerPassword').value;
        
        fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, email, password })
        })
        .then(response => response.json())
        .then(data => alert(data.message))
        .catch(error => console.error('Error:', error));
    });

    // Login form submission
    document.getElementById('loginForm').addEventListener('submit', function(event) {
        event.preventDefault();
        const email = document.getElementById('loginEmail').value;
        const password = document.getElementById('loginPassword').value;

        fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            if (data.message === 'Login successful') {
                sessionStorage.setItem('loggedIn', true); // Track login status
            }
        })
        .catch(error => console.error('Error:', error));
    });

    // Ask a question
    document.querySelector('button[onclick="askAssistant()"]').addEventListener('click', function() {
        const query = document.getElementById('user-input').value;
        fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query })
        })
        .then(response => response.json())
        .then(data => {
            document.getElementById('response').innerText = data.response;
        })
        .catch(error => console.error('Error:', error));
    });

    // Fetch query history
    document.getElementById('fetchHistory').addEventListener('click', function() {
        if (!sessionStorage.getItem('loggedIn')) {
            alert('You need to log in to see your history.');
            return;
        }

        fetch('/history', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            const historyOutput = document.getElementById('historyOutput');
            historyOutput.innerHTML = '';
            data.forEach(item => {
                const entry = document.createElement('div');
                entry.innerHTML = `<strong>Query:</strong> ${item.query}<br><strong>Response:</strong> ${item.response}<br><strong>Timestamp:</strong> ${new Date(item.timestamp).toLocaleString()}<br><br>`;
                historyOutput.appendChild(entry);
            });
        })
        .catch(error => console.error('Error:', error));
    });
});
