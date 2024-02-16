function handler(event) {
  if (!event.request.headers.hasOwnProperty('host')) {
    return {
      statusCode: 404,
      statusDescription: 'Not Found',
    }
  }

  if (!event.request.headers.host.value.startsWith('www.')) {
    return {
      statusCode: 301,
      statusDescription: 'Moved Permanently',
      headers: {
        location: {
          value: `https://www.${event.request.headers.host.value}${event.request.uri}`,
        },
      },
    }
  }

  return event.request
}
