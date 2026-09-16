(() => {
  'use strict';

  const page = document.getElementById('coursePage');
  const error = document.getElementById('courseError');
  const type = document.getElementById('courseType');
  const title = document.getElementById('courseTitle');
  const description = document.getElementById('courseDescription');
  if (!page || !error || !type || !title || !description) return;

  const slugPattern = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
  const params = new URLSearchParams(window.location.search);
  const requestedId = params.get('id');

  const failClosed = () => {
    page.hidden = true;
    error.hidden = false;
    document.title = 'Course unavailable — Teaching Hub';
  };

  const validPublishedCourse = (course) => course &&
    typeof course === 'object' &&
    course.published === true &&
    Number.isInteger(course.order) &&
    typeof course.id === 'string' && slugPattern.test(course.id) &&
    typeof course.type === 'string' && course.type.trim() !== '' &&
    typeof course.title === 'string' && course.title.trim() !== '' &&
    typeof course.description === 'string' && course.description.trim() !== '';

  if (!requestedId || !slugPattern.test(requestedId)) {
    failClosed();
    return;
  }

  fetch('./data/teaching.json', { cache: 'no-store' })
    .then((response) => {
      if (!response.ok) throw new Error('Catalogue request failed');
      return response.json();
    })
    .then((data) => {
      if (!data || data.schema_version !== 1 || !Array.isArray(data.courses)) {
        throw new Error('Unsupported catalogue schema');
      }

      const published = data.courses.filter((course) => course && course.published === true);
      if (!published.every(validPublishedCourse)) throw new Error('Invalid published course');

      const course = published.find((item) => item.id === requestedId);
      if (!course) throw new Error('Course is not published');

      type.textContent = course.type;
      title.textContent = course.title;
      description.textContent = course.description;
      document.title = `${course.title} — Teaching Hub`;
      error.hidden = true;
      page.hidden = false;
    })
    .catch(failClosed);
})();
