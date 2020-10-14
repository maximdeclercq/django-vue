/* Routing logic */
window.addEventListener('popstate', function () {
  console.log(href)
  history.pushState({}, '', href)
  $.ajax({
    type: 'GET',
    url: href,
    complete: function (jqXHR, textStatus) {
      console.log(jqXHR)
      updateElements(jqXHR.content)
      // let partialViewsReplaceId = jqXHR.getResponseHeader('partial-views-replace-id')
      // if (partialViewsReplaceId === null) {
      // Not a partial view endpoint
      //   window.dispatchEvent(new Event('popstate'))
      //   return
      // }
      // console.log('test')
    },
  })
})

/* Rehook logic */
function registerAjax() {
  $('[data-partial-link]').each(function () {
    let element = $(this)
    element.off('click.ajax')
    element.on('click.ajax', function (e) {
      e.preventDefault()
      let url = element.data('ajax-url') || element.prop('href') || element.prop('action') || window.location.href
      element.prop('disabled', true)
      $.get({ url: url })
        .done(function (data) {
          element.prop('disabled', false)
          updateElements(data, url)
        })
        .fail(function (data) {})
    })
  })
  $('[data-partial-form]').each(function () {
    let element = $(this)
    element.ajaxForm({
      beforeSubmit: function (formData, jqForm, options) {
        element.children().prop('disabled', true)
      },
      complete: function (data, status) {
        updateElements(data)
        element.children().prop('disabled', false)
      },
    })
  })
}

/* Replacement logic */
function updateElements(data) {
  for (let key in data) {
    if (data.hasOwnProperty(key)) {
      $(`*[data-partial-id="${key}"]`).replaceWith(data[key])
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
