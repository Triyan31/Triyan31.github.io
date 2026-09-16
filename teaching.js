(() => {
  'use strict';

  const catalogue = document.getElementById('teachingCatalogue');
  const errorState = document.getElementById('teachingCatalogueError');
  if (!catalogue || !errorState) return;

  const slugPattern = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

  const failClosed = () => {
    catalogue.replaceChildren();
    errorState.hidden = false;
  };

  const isValidCourse = (course) => {
    return course &&
      typeof course === 'object' &&
      course.published === true &&
      Number.isInteger(course.order) &&
      typeof course.id === 'string' && slugPattern.test(course.id) &&
      typeof course.type === 'string' && course.type.trim() !== '' &&
      typeof course.title === 'string' && course.title.trim() !== '' &&
      typeof course.description === 'string' && course.description.trim() !== '';
  };

  const createCourseCard = (course, position) => {
    const link = document.createElement('a');
    link.className = 'course reveal visible';
    link.href = `./course.html?id=${encodeURIComponent(course.id)}`;
    link.setAttribute('aria-label', `Open ${course.title} course`);

    const number = document.createElement('div');
    number.className = 'course-no';
    number.textContent = String(position + 1).padStart(2, '0');

    const body = document.createElement('div');
    const type = document.createElement('span');
    type.className = 'course-type';
    type.textContent = course.type;
    const title = document.createElement('h3');
    title.textContent = course.title;
    const description = document.createElement('p');
    description.textContent = course.description;
    body.append(type, title, description);

    const arrow = document.createElement('span');
    arrow.className = 'course-arrow';
    arrow.setAttribute('aria-hidden', 'true');
    arrow.textContent = '↗';

    link.append(number, body, arrow);
    return link;
  };

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
      if (!published.every(isValidCourse)) throw new Error('Invalid published course');

      published.sort((a, b) => a.order - b.order);
      catalogue.replaceChildren();

      if (published.length === 0) {
        const empty = document.createElement('p');
        empty.className = 'teaching-state';
        empty.textContent = 'No public courses are available yet.';
        catalogue.append(empty);
        return;
      }

      published.forEach((course, index) => catalogue.append(createCourseCard(course, index)));
    })
    .catch(failClosed);
})();
