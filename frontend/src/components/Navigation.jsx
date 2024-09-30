import { Link } from "react-router-dom"

import '../App.css'

export default function Navigation() {
  return (
     <nav className="navbar navbar-expand-lg navbar-light bg-light fixed-top">
     <div className="container">
     <Link id="link" to="/inicio">Monitoreo Forrajero
     </Link>
       <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
         <span className="navbar-toggler-icon"></span>
       </button>
       <div className="collapse navbar-collapse" id="navbarNav">
         <ul className="navbar-nav ms-auto">
            <Link id="link" to="/inicio">Inicio
            </Link>
            <Link id="link" to="/materiaseca">Estimaciones 
            </Link>
            <Link id="link" to="#">Contacto
            </Link>
            <Link id="link" to="#">Equipo 
            </Link>
         </ul>
       </div>
     </div>
   </nav>
  )
}
