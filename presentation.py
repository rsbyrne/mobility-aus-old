from IPython.display import Markdown
def markprint(x):
    display(Markdown(x))
    
def hide_code_button():
    from IPython.display import HTML, display

    display(HTML('''<script>
        code_show=true; 
        function code_toggle() {
         if (code_show){
         $('div.input').hide();
         } else {
         $('div.input').show();
         }
         code_show = !code_show
        } 
        $( document ).ready(code_toggle);
        </script>
        <form action="javascript:code_toggle()"><input type="submit" value="Click here to toggle on/off the raw code."></form>'''))