export const VERTICAL_ROWS_BY_PAPER_SIZE = {
  a3: 4,
  a4: 4,
  b5: 2,
  a4l: 2,
};

export const VERTICAL_COLUMNS = 2;

export const getVerticalRows = (paperSize) => (
  VERTICAL_ROWS_BY_PAPER_SIZE[paperSize.toLowerCase()]
  ?? VERTICAL_ROWS_BY_PAPER_SIZE.a4
);

export const isVerticalOperation = (params) => (
  params.command_type === 'ope' && params.vertical === true
);
