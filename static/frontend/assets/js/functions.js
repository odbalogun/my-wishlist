/*global jQuery */
(function($) {
  "use strict";

  /* ------------------  LOADING SCREEN ------------------ */

  $(window).on("load", function() {
      $(".preloader").fadeOut(5000).remove();
      $('.toast').addClass('on');
      $('.toast-failed').addClass('on');
  });

  /* ------------------  Background INSERT ------------------ */

  var $bgSection = $(".bg-section"),
      $bgPattern = $(".bg-pattern"),
      $colBg = $(".col-bg");

  $bgSection.each(function() {
      var bgSrc = $(this).children("img").attr("src");
      var bgUrl = "url(" + bgSrc + ")";
      $(this).parent().css("backgroundImage", bgUrl);
      $(this).parent().addClass("bg-section");
      $(this).remove();
  });

  $bgPattern.each(function() {
      var bgSrc = $(this).children("img").attr("src");
      var bgUrl = "url(" + bgSrc + ")";
      $(this).parent().css("backgroundImage", bgUrl);
      $(this).parent().addClass("bg-pattern");
      $(this).remove();
  });

  $colBg.each(function() {
      var bgSrc = $(this).children("img").attr("src");
      var bgUrl = "url(" + bgSrc + ")";
      $(this).parent().css("backgroundImage", bgUrl);
      $(this).parent().addClass("col-bg");
      $(this).remove();
  });

  /* ------------------  NAV MODULE  ------------------ */
  
  var $moduleIcon = $(".module-icon"),
      $moduleCancel = $(".module-cancel");

  $moduleIcon.on("click", function(e) {
      $(this).parent().siblings().removeClass("module-active"); // Remove the class .active form any sibiling.
      $(this).parent(".module").toggleClass("module-active"); //Add the class .active to parent .module for this element.
      e.stopPropagation();
  });
  // If Click on [ Search-cancel ] Link
  $moduleCancel.on("click", function(e) {
      $(".module").removeClass("module-active");
      e.stopPropagation();
      e.preventDefault();
  });

  $(".side-nav-icon").on("click", function() {
      if ($(this).parent().hasClass("module-active")) {
          $(".wrapper").addClass("hamburger-active");
          $(this).addClass("module-hamburger-close");
      } else {
          $(".wrapper").removeClass("hamburger-active");
          $(this).removeClass("module-hamburger-close");
      }
  });

  // If Click on [ Document ] and this click outside [ hamburger panel ]
  $(document).on("click", function(e) {
      if ($(e.target).is(".hamburger-panel,.hamburger-panel .list-links,.hamburger-panel .list-links a,.hamburger-panel .social-share,.hamburger-panel .social-share a i,.hamburger-panel .social-share a,.hamburger-panel .copywright") === false) {
          $(".wrapper").removeClass("page-transform"); // Remove the class .active form .module when click on outside the div.
          $(".module-side-nav").removeClass("module-active");
          e.stopPropagation();
      }
  });

  // If Click on [ Document ] and this click outside [ module ]
  $(document).on("click", function(e) {
      if ($(e.target).is(".module, .module-content, .search-form input,.cart-control .btn,.cart-overview a.cancel,.cart-box,.select-box") === false) {
          $module.removeClass("module-active"); // Remove the class .active form .module when click on outside the div.
          e.stopPropagation();
      }
  });

  /* ------------------  MOBILE MENU ------------------ */

  var $dropToggle = $("ul.dropdown-menu [data-toggle=dropdown]"),
      $module = $(".module");

  $dropToggle.on("click", function(event) {
      event.preventDefault();
      event.stopPropagation();
      $(this).parent().siblings().removeClass("open");
      $(this).parent().toggleClass("open");
  });

  $module.on("click", function() {
      $(this).toggleClass("toggle-module");
  });

  $module.find("input.form-control", ".btn", ".module-cancel").click(function(e) {
      e.stopPropagation();
  });

  /* ------------------  COUNTER UP ------------------ */

  $(".counting").counterUp({
      delay: 10,
      time: 1000
  });

  /* ------------------ COUNTDOWN DATE ------------------ */

  $(".countdown").each(function() {
      var $countDown = $(this),
          countDate = $countDown.data("count-date"),
          newDate = new Date(countDate);
      $countDown.countdown({
          until: newDate,
          format: "dHMS"
      });
  });

  /* ------------------  AJAX CAMPAIGN MONITOR  ------------------ */

  $("#campaignmonitor").submit(function(e) {
      e.preventDefault();
      $.getJSON(this.action + "?callback=?", $(this).serialize(), function(data) {
          if (data.Status === 400) {
              alert("Error: " + data.Message);
          } else {
              // 200
              alert("Success: " + data.Message);
          }
      });
  });


  /* ------------------ OWL CAROUSEL ------------------ */

  var $productsSlider = $(".products-slider");

  $(".carousel").each(function() {
      var $Carousel = $(this);
      $Carousel.owlCarousel({
          loop: $Carousel.data("loop"),
          autoplay: $Carousel.data("autoplay"),
          margin: $Carousel.data("space"),
          nav: $Carousel.data("nav"),
          dots: $Carousel.data("dots"),
          center: $Carousel.data("center"),
          dotsSpeed: $Carousel.data("speed"),
          responsive: {
              0: {
                  items: 1
              },
              600: {
                  items: $Carousel.data("slide-rs")
              },
              1000: {
                  items: $Carousel.data("slide")
              }
          }
      });
  });

  $productsSlider.owlCarousel({
      thumbs: true,
      thumbsPrerendered: true,
      loop: true,
      margin: 0,
      autoplay: false,
      nav: false,
      dots: false,
      dotsSpeed: 200,
      responsive: {
          0: {
              items: 1
          },
          600: {
              items: 1
          },
          1000: {
              items: 1
          }
      }
  });

  /* ------------------ MAGNIFIC POPUP ------------------ */

  var $imgPopup = $(".img-popup");

  $imgPopup.magnificPopup({
      type: "image"
  });
  $(".img-gallery-item").magnificPopup({
      type: "image",
      gallery: {
          enabled: true
      }
  });

  /* ------------------  MAGNIFIC POPUP VIDEO ------------------ */

  $(".popup-video,.popup-gmaps").magnificPopup({
      disableOn: 700,
      mainClass: "mfp-fade",
      removalDelay: 0,
      preloader: false,
      fixedContentPos: false,
      type: "iframe",
      iframe: {
          markup: '<div class="mfp-iframe-scaler">' + '<div class="mfp-close"></div>' + '<iframe class="mfp-iframe" frameborder="0" allowfullscreen></iframe>' + "</div>",
          patterns: {
              youtube: {
                  index: "youtube.com/",
                  id: "v=",
                  src: "//www.youtube.com/embed/%id%?autoplay=1"
              }
          },
          srcAction: "iframe_src"
      }
  });

  /* ------------------  SWITCH GRID ------------------ */

  var $switchList = $("#switch-list"),
      $switchGrid = $("#switch-grid"),
      $productItem = $(".product-item");

  $switchList.on("click", function(event) {
      event.preventDefault();
      $(this).addClass("active");
      $(this).siblings().removeClass("active");
      $productItem.each(function() {
          $(this).addClass("product-list");
          $(this).removeClass("product-grid");
      });
  });

  $switchGrid.on("click", function(event) {
      event.preventDefault();
      $(this).addClass("active");
      $(this).siblings().removeClass("active");
      $productItem.each(function() {
          $(this).removeClass("product-list");
          $(this).addClass("product-grid");
      });
  });

  /* ------------------  BACK TO TOP ------------------ */

  var backTop = $("#back-to-top");

  if (backTop.length) {
      var scrollTrigger = 200, // px
          backToTop = function() {
              var scrollTop = $(window).scrollTop();
              if (scrollTop > scrollTrigger) {
                  backTop.addClass("show");
              } else {
                  backTop.removeClass("show");
              }
          };

      backToTop();

      $(window).on("scroll", function() {
          backToTop();
      });

      backTop.on("click", function(e) {
          e.preventDefault();
          $("html,body").animate({
              scrollTop: 0
          }, 700);
      });
  }

  /* ------------------ BLOG FLITER ------------------ */

  var $blogFilter = $(".blog-filter"),
      blogLength = $blogFilter.length,
      blogFinder = $blogFilter.find("a"),
      $blogAll = $("#enrty-all");

  // init Isotope For shop
  blogFinder.on("click", function(e) {
      e.preventDefault();
      $blogFilter.find("a.active-filter").removeClass("active-filter");
      $(this).addClass("active-filter");
  });

  if (blogLength > 0) {
      $blogAll.imagesLoaded().progress(function() {
          $blogAll.isotope({
              filter: "*",
              animationOptions: {
                  duration: 750,
                  itemSelector: ".blog-entry",
                  easing: "linear",
                  queue: false
              }
          });
      });
  }

  blogFinder.on("click", function(e) {
      e.preventDefault();
      var $selector = $(this).attr("data-filter");
      $blogAll.imagesLoaded().progress(function() {
          $blogAll.isotope({
              filter: $selector,
              animationOptions: {
                  duration: 750,
                  itemSelector: ".blog-entry",
                  easing: "linear",
                  queue: false
              }
          });
          return false;
      });
  });

  /* ------------------  SCROLL TO ------------------ */

  var aScroll = $('a[data-scroll="scrollTo"]');

  aScroll.on("click", function(event) {
      var target = $($(this).attr("href"));
      if (target.length) {
          event.preventDefault();
          $("html, body").animate({
              scrollTop: target.offset().top
          }, 1000);
          if ($(this).hasClass("menu-item")) {
              $(this).parent().addClass("active");
              $(this).parent().siblings().removeClass("active");
          }
      }
  });

  /* ------------------ SLIDER RANGE ------------------ */

  var $sliderRange = $("#slider-range"),
      $sliderAmount = $("#amount");

  $sliderRange.slider({
      range: true,
      min: 0,
      max: 500,
      values: [
          50, 300
      ],
      slide: function(event, ui) {
          $sliderAmount.val("$" + ui.values[0] + " - $" + ui.values[1]);
      }
  });

  $sliderAmount.val("$" + $sliderRange.slider("values", 0) + " - $" + $sliderRange.slider("values", 1));

  /* ------------------ GOOGLE MAP ------------------ */

  $(".googleMap").each(function() {
      var $gmap = $(this);
      $gmap.gMap({
          address: $gmap.data("map-address"),
          zoom: $gmap.data("map-zoom"),
          maptype: $gmap.data("map-type"),
          markers: [{
              address: $gmap.data("map-address"),
              maptype: $gmap.data("map-type"),
              html: $gmap.data("map-info"),
              icon: {
                  image: $gmap.data("map-maker-icon"),
                  iconsize: [
                      76, 61
                  ],
                  iconanchor: [76, 61]
              }
          }]
      });
  });

  /* ------------------ WIDGET CATEGORY TOGGLE MENU  ------------------ */

  var $widgetCategoriesLink = $(".widget-categories2 .main--list > li > a");

  $widgetCategoriesLink.on("click", function(e) {
      $(this).parent().siblings().removeClass("active");
      $(this).parent().toggleClass("active");
      e.stopPropagation();
      e.preventDefault();
  });

  /* ------------------  ToolTIP ------------------ */

  $('[data-toggle="tooltip"]').tooltip();

  /* ------------------ ANIMATION ------------------ */

  new WOW().init();

  /* ------------------  PARALLAX EFFECT ------------------ */

  siteFooter();
  $(window).resize(function() {
      siteFooter();
  });

  function siteFooter() {
      var siteContent = $("#wrapperParallax");
      var contentParallax = $(".contentParallax");

      var siteFooter = $("#footerParallax");
      var siteFooterHeight = siteFooter.height();

      siteContent.css({
          "margin-bottom": siteFooterHeight
      });
  }

  /* ------------------ EQUAL IMAGE AND CONTENT CATEGORY ------------------ */

  var $categoryImg = $(".category-5 .category--img"),
      $categoryContent = $(".category-5 .category--content"),
      $categoryContentHeight = $categoryContent.outerHeight();

  $categoryImg.css("height", $categoryContentHeight);

  /* ------------------ PRODUCT QANTITY ------------------ */

  var $productQuantity = $('.product-quantity');

  $productQuantity.on('click', '.plus', function(e) {
      var $input = $(this).prev('input.qty');
      var val = parseInt($input.val());
      var step = $input.attr('step');
      step = 'undefined' !== typeof(step) ? parseInt(step) : 1;
      $input.val(val + step).change();
  });

  $productQuantity.on('click', '.minus',function(e) {
      var $input = $(this).next('input.qty');
      var val = parseInt($input.val());
      var step = $input.attr('step');
      step = 'undefined' !== typeof(step) ? parseInt(step) : 1;
      if (val > 0) {
          $input.val(val - step).change();
      }
  });

  $(function () {
  
    $('.close').click(function() {
      $('.toast').removeClass('on');
    });
    $('.failed-close').click(function() {
        $('.toast-failed').removeClass('on');
      });
  });

})(jQuery);