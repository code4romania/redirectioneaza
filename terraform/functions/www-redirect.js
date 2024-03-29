function handler(event) {
  if (!event.request.headers.hasOwnProperty('host')) {
    return {
      statusCode: 404,
      statusDescription: 'Not Found',
    }
  }

  if (event.request.headers.host.value.startsWith('www.')) {
    return {
      statusCode: 301,
      statusDescription: 'Moved Permanently',
      headers: {
        location: {
          value: `https://${event.request.headers.host.value.replace('www.', '')}${event.request.uri}`,
        },
      },
    }
  }

  return event.request
}
