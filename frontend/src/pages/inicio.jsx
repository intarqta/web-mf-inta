import React from 'react';
import '../components/assets/slider.css';
import ImageSlider from '../components/Slider';

function Inicio() {
return (
  <div className="App">
    <header className="App-header">
    </header>
    <main>
      <section>
      <ImageSlider />
      </section>
      
    </main>
    <footer>
      <p>&copy; 2024 Portal de Monitoreo Forrajero. Todos los derechos reservados.</p>
    </footer>
  </div>
);
}

export default Inicio;