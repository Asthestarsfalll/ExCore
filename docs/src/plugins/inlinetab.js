//tests

const visit = require('unist-util-visit');

const plugin = (options) => {
  const transformer = async (ast) => {
    let number = 1;
    visit(ast, 'heading', (node) => {
      if (node.depth === 2 && node.children.length > 0) {
        if (node.children[0].type === 'text') {
          node.children[0].value = `Section ${number}. ${node.children[0].value}`;
        } else {
          node.children.unshift({
            type: 'text',
            value: `Section ${number}. `,
          });
        }
        number++;
      }
    });
  };
  return transformer;
};

module.exports = plugin;

//tests