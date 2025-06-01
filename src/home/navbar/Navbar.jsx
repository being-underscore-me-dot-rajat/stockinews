import React from 'react'
import './Navbar.css'
import { useNavigate } from 'react-router-dom'

export default function Navbar() {

  const navigate=useNavigate()

  const handleogoclick=()=>{
    navigate('/dashboard');
  }

  return (
    <>
        <nav className="navbar">
            <div className="container-fluid">
                <a className="navbar-brands" onClick={handleogoclick}>
                    <img id='logo_img' src='images/logo.png' alt='asdasd'/>
                    Stock in News
                </a>
            </div>
        </nav>
    </>
  )
}
