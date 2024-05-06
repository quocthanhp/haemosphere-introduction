<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, shrink-to-fit=no">
    <title>Haemosphere</title>
    <link rel="stylesheet" href="//cdn.jsdelivr.net/npm/bootstrap@5.1.0/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="css/Footer-Clean.css">
    <link rel="stylesheet" href="css/styles.css">
<link
        type="text/css"
        rel="stylesheet"
        href="//unpkg.com/bootstrap/dist/css/bootstrap.min.css"
/>

<link
        type="text/css"
        rel="stylesheet"
        href="//unpkg.com/bootstrap-vue@latest/dist/bootstrap-vue.css"
/>
<script src="//polyfill.io/v3/polyfill.min.js?features=es2015%2CIntersectionObserver"></script>
<script src="//unpkg.com/vue@latest/dist/vue.js"></script>
<script src="//unpkg.com/bootstrap-vue@latest/dist/bootstrap-vue.js"></script>
<link type="text/css" rel="stylesheet" href="//unpkg.com/bootstrap-vue@latest/dist/bootstrap-vue-icons.min.css"/>
<script src="//unpkg.com/bootstrap-vue@latest/dist/bootstrap-vue-icons.min.js"></script>
    <style>
body {
  display: flex;
  min-height: 100vh;
  flex-direction: column;
}

main {
  flex: 1;
}

header {
  position: relative;
  background-color: black;
  height: 75vh;
  min-height: 25rem;
  width: 100%;
  overflow: hidden;
}

header video {
  position: absolute;
  top: 50%;
  left: 50%;
  min-width: 100%;
  min-height: 100%;
  width: auto;
  height: auto;
  z-index: 0;
  -ms-transform: translateX(-50%) translateY(-50%);
  -moz-transform: translateX(-50%) translateY(-50%);
  -webkit-transform: translateX(-50%) translateY(-50%);
  transform: translateX(-50%) translateY(-50%);
}

header .container {
  position: relative;
  z-index: 2;
}

header .overlay {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  width: 100%;
  background-color: black;
  opacity: 0.5;
  z-index: 1;
}

/* Media Query for devices withi coarse pointers and no hover functionality */

/* This will use a fallback image instead of a video for devices that commonly do not support the HTML5 video element */

@media (pointer: coarse) and (hover: none) {
  header {
    background: url('https://source.unsplash.com/XT5OInaElMw/1600x900') black no-repeat center center scroll;
  }

  header video {
    display: none;
  }
}


    </style>
</head>

<body style="opacity: 1;filter: blur(0px);padding-top: 10px;padding-right: 10px;padding-left: 10px;">
<div id="app">
<header>

  <!-- This div is  intentionally blank. It creates the transparent black overlay over the video which you can modify in the CSS -->
  <div class="overlay"></div>

  <!-- The HTML5 video element that will create the background video on the header -->
  <video playsinline="playsinline" autoplay="autoplay" muted="muted" loop="loop">
    <source src="images/video.mp4" type="video/mp4">
  </video>
    <nav class="navbar navbar-light navbar-expand-md sticky-top"
         style="color: var(--bs-blue);background: linear-gradient(162deg, black 0%, white 0%, rgb(255,204,102) 58%);box-shadow: 0px 0px 8px 4px var(--bs-gray-800);margin: 30px;height: 78px;padding: 0px 0px;padding-left: 0px;border-width: 0px;border-style: outset;">
        <div class="container-fluid"><a class="navbar-brand" href="#"></a>
            <button data-bs-toggle="collapse" class="navbar-toggler" data-bs-target="#navcol-1"><span
                    class="visually-hidden">Toggle navigation</span><span class="navbar-toggler-icon"></span></button>
            <div class="collapse navbar-collapse" id="navcol-1">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item text-start"><a class="nav-link text-start" href="/aboutpage">About</a></li>
                    <li class="nav-item text-start"><a class="nav-link text-start" href="#">Searches</a></li>
                    <li class="nav-item text-start"><a class="nav-link text-start" href="#">Datasets</a></li>
                    <li class="nav-item text-start"><a class="nav-link text-start" href="#">Genes</a></li>
                    <li class="nav-item text-start"><a class="nav-link text-start" href="#">Login</a></li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container" style="text-align: center;box-shadow: 0px 0px;"><img src="images/pic.png" style="width: 305px;height: 300px;padding: 1px;"></div>
    <div class="container" style="text-align: center;width: 1324px;">
<div class=" input-group mb-3">
  <input type="search" class="form-control" placeholder="Search Haemosphere" aria-label="Recipient's username" aria-describedby="button-addon2">
  <button class="btn btn-outline-secondary" type="button" id="button-addon2">Search</button>
</div>
    </div>

    <!-- The header content -->
</header>
    <footer class="d-xxl-flex align-items-xxl-start footer-clean fixed-bottom">
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-sm-4 col-md-3 item">
                    <h3>Citation</h3>
                    <ul>
                        <li></li>
                    </ul>
                    <p style="font-size: 12px;"><a href="https://doi.org/10.1093/nar/gky1020">Haemopedia RNA-seq: a
                        database of gene expression during haematopoiesis in mice and humans&nbsp;<em>Nucl. Acids
                            Res.</em>&nbsp;(2019)</a>&nbsp;</p>
                </div>
                <div class="col-sm-4 col-md-3 item">
                    <h3>Version</h3>
                    <ul></ul>
                    <p style="font-size: 12px;">{{Version_Number}}</p>
                </div>
                <div class="col-sm-4 col-md-3 item">
                    <h3>Haemosphere</h3>
                    <ul>
                        <li><a href="#" style="font-size: 12px;">About</a></li>
                        <li><a href="#" style="font-size: 12px;">Searches</a></li>
                        <li><a href="#" style="font-size: 12px;">Datasets</a></li>
                    </ul>
                </div>
                <div class="col-lg-3 item social">
                    <p class="copyright"><img src="images/wehi-logo.png"></p>
                </div>
            </div>
        </div>
    </footer>
    <script src="//cdn.jsdelivr.net/npm/bootstrap@5.1.0/dist/js/bootstrap.bundle.min.js"></script>


</div>
<script>
    window.app = new Vue({
        el: '#app',
        data: {Version_Number: 'Version Number'}
    })
</script>

</body>

</html>