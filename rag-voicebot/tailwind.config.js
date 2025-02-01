// tailwind.config.js
module.exports = {
    content: [
        "./src/**/*.{js,jsx,ts,tsx}",
    ],
    theme: {
        extend: {
            animation: {
                bounce: 'bounce 1s infinite',
            },
        },
    },
    plugins: [],
}