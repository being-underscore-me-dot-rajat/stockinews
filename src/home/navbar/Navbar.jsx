import React from 'react'
import './Navbar.css'

export default function Navbar() {
  return (
    <>
        <nav className="navbar">
            <div className="container-fluid">
                <a className="navbar-brands" href='/'>
                    <img id='logo_img' src='images/logo.png' alt='asdasd'/>
                    Stock in News
                </a>
            </div>
        </nav>
    </>
  )
}
