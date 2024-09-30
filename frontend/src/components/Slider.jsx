import { useState } from 'react';
import Carousel from 'react-bootstrap/Carousel';

import img1 from './assets/images/img-slider-1.jpg'
// import img2 from '../IMG/inovacao-no-agronegocio.jpg'
// import img3 from '../IMG/telefono.png'

import { Link } from 'react-router-dom';


function ControlledCarousel() {
  const [index, setIndex] = useState(0);

  const handleSelect = (selectedIndex) => {
    setIndex(selectedIndex);
  };

  return (
    <div>
        <Carousel activeIndex={index} onSelect={handleSelect}>
            <Carousel.Item>
                <Link to={'/coberturas'}>
                <img style={{width:'100vw'}} src={img1} text="Mapas de coberturas" />
                </Link>
                <Carousel.Caption>
                <h1>Portal de Monitoreo Forrajero</h1>
                <p>
                Utilizando tecnología de teledetección, nuestro portal proporciona herramientas avanzadas para el monitoreo y análisis de forrajes, optimizando la producción y la gestión de recursos.
                </p>
                </Carousel.Caption>
            </Carousel.Item>
        </Carousel>
    </div>
  );
}

export default ControlledCarousel;