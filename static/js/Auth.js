// Authentication Module
const Auth = {
    token: localStorage.getItem('access_token'),
    
    isAuthenticated() {
        return !!this.token;
    },
    
    async register(userData) {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(userData)
        });
        
        if (response.ok) {
            const data = await response.json();
            this.token = data.access_token;
            localStorage.setItem('access_token', this.token);
            return true;
        }
        return false;
    },
    
    async login(username, password) {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        if (response.ok) {
            const data = await response.json();
            this.token = data.access_token;
            localStorage.setItem('access_token', this.token);
            return true;
        }
        return false;
    },
    
    logout() {
        this.token = null;
        localStorage.removeItem('access_token');
        window.location.href = '/';
    },
    
    getAuthHeader() {
        return { 'Authorization': `Bearer ${this.token}` };
    }
};