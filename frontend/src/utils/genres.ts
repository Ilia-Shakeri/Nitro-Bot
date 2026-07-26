export const GENRE_TREE: Readonly<Record<string, readonly string[]>> = {
  'HipHop / Rap [Urban]': ['Trap', 'Drill', 'Boom Bap', 'Gangsta Rap', 'Conscious', 'Cloud Rap'],
  Pop: ['Dance Pop', 'Synth Pop', 'Indie Pop', 'Electropop', 'K-Pop'],
  Rock: ['Alternative', 'Indie Rock', 'Hard Rock', 'Punk', 'Post-Rock'],
  'Electronic / Dance': ['House', 'Techno', 'Trance', 'Dubstep', 'Drum & Bass', 'EDM'],
  'R&B / Soul': ['Contemporary R&B', 'Neo-Soul', 'Funk'],
  Classical: ['Orchestral', 'Piano', 'Opera', 'Chamber'],
  Jazz: ['Smooth Jazz', 'Bebop', 'Fusion', 'Swing'],
  Folk: ['Indie Folk', 'Singer-Songwriter', 'Americana'],
  Country: ['Modern Country', 'Bluegrass', 'Country Pop'],
  Reggae: ['Roots', 'Dancehall', 'Dub'],
  Metal: ['Heavy Metal', 'Death Metal', 'Black Metal', 'Metalcore'],
  World: ['Latin', 'Afrobeat', 'Persian', 'Arabic'],
};

export const changeMainGenre = (genre: string) => ({
  genre,
  subGenre: '',
});

export const validSubGenre = (genre: string, subGenre: string) =>
  !subGenre || Boolean(GENRE_TREE[genre]?.includes(subGenre));
