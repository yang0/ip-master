(() => {
  const library = location.pathname.split('/assets/')[1]?.split('/')[0];
  const repositories = {
    'readme': 'https://github.com/yang0/ip-master',
    'visual-skill-hub': 'https://github.com/yang0/ip-master',
    'built-in-character-library': 'https://github.com/yang0/ip-master',
    'layout-library': 'https://github.com/nevertoday/350-layout-compositions',
    'gpt-image-2-case-library': 'https://github.com/freestylefly/awesome-gpt-image-2',
    'baoyu-skill-library': 'https://github.com/JimLiu/baoyu-skills',
    'vsc-skill-library': 'https://github.com/vibeshotclub/vsc-skills',
    'couple-photo-library': 'https://github.com/yang0/couple-photo',
    'xiaohei-skill-library': 'https://github.com/helloianneo/ian-xiaohei-illustrations',
    'guizang-skill-library': 'https://github.com/op7418/guizang-ppt-skill',
    'gbro-skill-library': 'https://github.com/pyang5166/gbro-cover-design',
  };
  const url = repositories[library];
  if (library === 'baoyu-skill-library') {
    document.querySelector('.top')?.remove();
  }
  const heading = document.querySelector('h1');
  if (!url || !heading || heading.querySelector('.github-title-link, .source')) return;
  const link = document.createElement('a');
  link.className = 'github-title-link';
  link.href = url;
  link.target = '_blank';
  link.rel = 'noopener';
  link.title = '在 GitHub 打开来源';
  link.setAttribute('aria-label', '在 GitHub 打开来源');
  link.innerHTML = '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true"><path fill="currentColor" d="M8 0a8 8 0 0 0-2.53 15.59c.4.07.55-.17.55-.38l-.01-1.49c-2.01.44-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82A7.63 7.63 0 0 1 8 4.73c.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48l-.01 2.19c0 .21.15.46.55.38A8 8 0 0 0 8 0Z"/></svg>';
  Object.assign(link.style, {
    display: 'inline-grid', placeItems: 'center', width: '20px', height: '20px',
    marginLeft: '8px', verticalAlign: 'middle', border: '1px solid currentColor',
    borderRadius: '4px', color: 'inherit', fontSize: '14px', lineHeight: '1',
    textDecoration: 'none', opacity: '.75',
  });
  link.addEventListener('mouseenter', () => { link.style.opacity = '1'; });
  link.addEventListener('mouseleave', () => { link.style.opacity = '.75'; });
  heading.append(link);
})();
