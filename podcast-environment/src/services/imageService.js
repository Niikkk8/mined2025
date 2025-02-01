const UNSPLASH_ACCESS_KEY = '8BxcGK5bLyBRAflS5Yt8PxL6jgPMf99xmdcI02CkX0s';

export const fetchBackgroundImages = async (keywords) => {
    try {
        const response = await fetch(
            `https://api.unsplash.com/search/photos?query=${keywords}&per_page=10&orientation=landscape`,
            {
                headers: {
                    Authorization: `Client-ID ${UNSPLASH_ACCESS_KEY}`
                }
            }
        );
        
        if (!response.ok) {
            throw new Error('Failed to fetch images');
        }
        
        const data = await response.json();
        return data.results.map(photo => photo.urls.regular);
    } catch (error) {
        console.error('Error fetching images:', error);
        return [];
    }
};