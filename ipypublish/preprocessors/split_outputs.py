import logging,copy
from nbconvert.preprocessors import Preprocessor
from nbformat.notebooknode import NotebookNode
import traitlets as traits
                
def merge(a, b, path=None,overwrite=True):
    """merges b into a
    
    Examples
    --------
    >>> merge({'a':{'b':1},'c':3},{'a':{'b':2}})
    {'a': {'b': 2}, 'c': 3}
    
    """
    if path is None: path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)],overwrite)
            elif a[key] == b[key]:
                pass # same leaf value
            elif overwrite:
                a[key] = b[key] # overwrite leaf value
            else:
                raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a
        
class SplitOutputs(Preprocessor):
    """ a preprocessor to split outputs into separate cells,
    merging the cell and output metadata, with output metadata taking priority
    
    """          
    
    split = traits.Bool(True,help="whether to split outputs").tag(config=True)
      
    def preprocess(self, nb, resources):
        
        if not self.split:
            return nb, resources
                
        logging.info('splitting outputs into separate cells') 

        final_cells = []
        for cell in nb.cells:
            
            if not cell.cell_type == "code":
                final_cells.append(cell)
                continue
            outputs = cell.pop("outputs")
            cell.outputs = []
            final_cells.append(cell)
            for output in outputs:
                meta = merge(copy.deepcopy(cell.metadata),output.get('metadata',{}))
                # don't need the code to output
                meta.get('ipub',NotebookNode({})).code = False
                if 'slide' in meta.get('ipub',NotebookNode({})):
                    meta.ipub.slide = True if meta.ipub.slide == 'new' else meta.ipub.slide
                new =  NotebookNode({
                    "cell_type": "code",
                    "source": '',
                    "execution_count": None,
                    "metadata":meta,
                    "outputs":[output]})
                final_cells.append(new)
            
        nb.cells = final_cells               
        
        return nb, resources