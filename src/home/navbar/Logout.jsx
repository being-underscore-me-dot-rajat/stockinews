import { useNavigate } from 'react-router-dom';
import { useEffect } from 'react';

export default function Logout() {
  const navigate = useNavigate();

  useEffect(() => {
    // Remove tokens and user info
    localStorage.removeItem('token');
    localStorage.removeItem('user');

    // Redirect to login
    navigate('/');
  }, [navigate]);

  return null; // or a loading spinner if you want
}
