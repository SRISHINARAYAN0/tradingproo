module.exports = {
  content: [
    './templates/**/*.html',
    './static/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#00a892',
          light: '#99f9ec',
          dark: '#30958a',
        },
        secondary: '#424242',
        accent: '#204165',
      },
    },
  },
  plugins: [
    require('daisyui'),
  ],
  safelist: [
    'bg-primary',
    'bg-primary-light',
    'bg-primary-dark',
    'text-primary',
    'text-primary-light',
    'text-primary-dark',
    'hover:bg-primary-dark',
  ],
  daisyui: {
    themes: [
      {
        light: {
          ...require('daisyui/src/colors/themes')['[data-theme=light]'],
          primary: '#ffffff', // Light green for light theme
          secondary: '#f0f0f0', // White for light theme
        },
      },
      {
        dark: {
          ...require('daisyui/src/colors/themes')['[data-theme=dark]'],
          primary: '#2a2a2a', // Dark grey for dark theme
          secondary: '#ff69b4', // Pink for subtle buttons in dark theme
        },
      },
    ],
  },
};
