(function () {
    'use strict';

    // swiper with navigation
    var swiper = new Swiper(".swiper-related-jobs", {
        navigation: {
            nextEl: ".swiper-button-next",
            prevEl: ".swiper-button-prev",
        },
        loop: true,
        breakpoints: {
            768: {
              slidesPerView: 2,
              spaceBetween: 40,
            },
            1024: {
              slidesPerView: 2,
              spaceBetween: 50,
            },
            1400: {
              slidesPerView: 2,
              spaceBetween: 50,
            },
        },
        autoplay: {
            delay: 1500,
            disableOnInteraction: false,
        }
    });

})();