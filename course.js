(() => {
  'use strict';

  const page = document.getElementById('coursePage');
  const error = document.getElementById('courseError');
  const type = document.getElementById('courseType');
  const title = document.getElementById('courseTitle');
  const description = document.getElementById('courseDescription');
  const profile = document.getElementById('courseProfile');
  const pending = document.getElementById('courseProfilePending');
  const focus = document.getElementById('courseFocus');
  const approach = document.getElementById('courseApproach');
  const tools = document.getElementById('courseTools');
  if (!page || !error || !type || !title || !description || !profile || !pending || !focus || !approach || !tools) return;

  const slugPattern = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
  const params = new URLSearchParams(window.location.search);
  const requestedId = params.get('id');

  const failClosed = () => {
    page.hidden = true;
    error.hidden = false;
    document.title = 'Course unavailable — Teaching Hub';
  };

  const validStringList = (value) => Array.isArray(value) && value.length > 0 &&
    value.every((item) => typeof item === 'string' && item.trim() !== '');

  const validProfile = (value) => value && typeof value === 'object' &&
    validStringList(value.focus_areas) &&
    validStringList(value.teaching_approach) &&
    validStringList(value.tools);

  const validPublishedCourse = (course) => course &&
    typeof course === 'object' &&
    course.published === true &&
    Number.isInteger(course.order) &&
    typeof course.id === 'string' && slugPattern.test(course.id) &&
    typeof course.type === 'string' && course.type.trim() !== '' &&
    typeof course.title === 'string' && course.title.trim() !== '' &&
    typeof course.description === 'string' && course.description.trim() !== '' &&
    (course.profile === undefined || validProfile(course.profile));

  const renderList = (target, items) => {
    const list = document.createElement('ul');
    list.className = 'course-profile-list';
    items.forEach((item) => {
      const li = document.createElement('li');
      li.textContent = item;
      list.append(li);
    });
    target.replaceChildren(list);
  };

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

      if (course.profile) {
        renderList(focus, course.profile.focus_areas);
        renderList(approach, course.profile.teaching_approach);
        renderList(tools, course.profile.tools);
        pending.hidden = true;
        profile.hidden = false;
      } else {
        profile.hidden = true;
        pending.hidden = false;
      }

      error.hidden = true;
      page.hidden = false;
    })
    .catch(failClosed);
})();
