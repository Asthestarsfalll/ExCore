interface TypicalText {
  text: string;
  delay: number;
}

const delay = 1500;

export const subtitles_and_delays: TypicalText[] = [
  {
    text: "Configuration/Registry System designed for deeplearning",
    delay: delay,
  },
  { text: "LazyConfig/LazyRegistry", delay: delay },
  { text: "Auto-completion, type-hinting and code navigation", delay: delay },
];

//should be in [0,12]
export const title_width: number = 5;
