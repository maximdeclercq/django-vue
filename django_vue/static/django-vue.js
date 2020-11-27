/* Return to previous page logic */
window.addEventListener('popstate', function (event) {
  if (event.state?.fluid) {
    $.get({ url: document.location })
      .done(function (data) {
        updateElements(data)
      })
      .fail(function (data) {
        window.location.reload()
      })
  } else {
    window.location.reload()
  }
})

/* Rehook logic */
function registerAjax() {
  $('a[data-fluid-target]').each(function () {
    let element = $(this)
    element.off('click.ajax')
    element.on('click.ajax', function (e) {
      e.preventDefault()
      element.prop('disabled', true)
      showLoading()
      let url = element.data('fluid-url') || element.prop('href') || element.prop('action') || window.location.href
      history.pushState({ fluid: true }, '', url)
      $.get({ url: url })
        .done(function (data) {
          updateElements(data)
          element.prop('disabled', false)
        })
        .fail(function (data) {
          hideLoading()
          console.log(data)
        })
    })
  })
  $('form[data-fluid-target]').each(function () {
    let element = $(this)
    element.ajaxForm({
      beforeSubmit: function (formData, jqForm, options) {
        showLoading()
        history.pushState({ fluid: true }, '', options.url)
        element.children().prop('disabled', true)
      },
      success: function (data, status) {
        updateElements(data)
        element.children().prop('disabled', false)
      },
      error: function (data, status) {
        history.back()
        element.children().prop('disabled', false)
      },
    })
  })
}

/* Loading logic */
function showLoading() {
  $('fluid-block').each(function () {
    let fluidBlock = $(this)
    fluidBlock.children().each(function () {
      // Wait 100ms before showing loading
      let loadingTimeout = 100
      let element = $(this)
      let overlay = $(`
      <div 
        class="d-flex justify-content-center align-items-center"
        style="position: absolute; background: rgba(0, 0, 0, 0.3);"
      >
        <div class="spinner-border" role="status">
          <span class="sr-only">Loading...</span>
        </div>
      </div>
    `)
        .width(element.width())
        .height(element.height())
        .css({ top: element.position().top, left: element.position().left })

      setTimeout(function () {
        // Check if element is still present
        if (fluidBlock && element) {
          overlay.hide()
          overlay.fadeIn(100)
          overlay.prependTo(fluidBlock)
        }
      }, loadingTimeout)
    })
  })
}

/* Element replacement logic */
function updateElements(data) {
  // Replace the entire body if the response is not a dictionary
  if (data.constructor !== Object) {
    document.open()
    document.write(data)
    document.close()
  }

  for (let key in data) {
    if (data.hasOwnProperty(key)) {
      $(`fluid-block[name="${key}"]`).replaceWith(data[key])
    }
  }
}

/* Setup AJAX for CSRF */
$.ajaxSetup({
  beforeSend: function (jqXHR, settings) {
    function getCookie(name) {
      let cookieValue = null
      if (document.cookie && document.cookie !== '') {
        let cookies = document.cookie.split(';')
        for (let i = 0; i < cookies.length; i++) {
          let cookie = jQuery.trim(cookies[i])
          if (cookie.substring(0, name.length + 1) === name + '=') {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
            break
          }
        }
      }
      return cookieValue
    }

    function csrfSafeMethod(method) {
      // these HTTP methods do not require CSRF protection
      return /^(GET|HEAD|OPTIONS|TRACE)$/.test(method)
    }

    function sameOrigin(url) {
      // test that a given url is a same-origin URL
      // url could be relative or scheme relative or absolute
      let host = document.location.host // host + port
      let protocol = document.location.protocol
      let sr_origin = '//' + host
      let origin = protocol + sr_origin
      // Allow absolute or scheme relative URLs to same origin
      return (
        url === origin ||
        url.slice(0, origin.length + 1) === origin + '/' ||
        url === sr_origin ||
        url.slice(0, sr_origin.length + 1) === sr_origin + '/' ||
        // or any other URL that isn't scheme relative or absolute i.e relative.
        !/^(\/\/|http:|https:).*/.test(url)
      )
    }

    if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
      jqXHR.setRequestHeader('x-csrftoken', getCookie('csrftoken'))
    }
  },
})

/* On document load */
$(function () {
  $(document).ajaxSuccess(function () {
    registerAjax()
  })

  registerAjax()
})
