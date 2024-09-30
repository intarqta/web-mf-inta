import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import MateriaSeca from './pages/MateriaSeca'
import Inicio from './pages/inicio'
import Navigation from './components/Navigation'

import './App.css'

function App() {
  
  return (
    <BrowserRouter>
    <Navigation />
      <Routes>
        <Route path='/' element={ <Navigate to="/inicio" /> } />
        <Route path='/materiaseca' element={<MateriaSeca />} />
        <Route path='/inicio' element={<Inicio />} />
      </Routes>
    </BrowserRouter>
   
  )
}

export default App
