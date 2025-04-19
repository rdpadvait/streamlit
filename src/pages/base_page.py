"""
Base page class for all application pages.
"""
import abc


class BasePage(abc.ABC):
    """Abstract base class that all pages should inherit from."""
    
    @abc.abstractmethod
    def render(self):
        """Render the page content."""
        pass
    
    @classmethod
    def render_page(cls):
        """
        Create an instance of the page and render it.
        This is the method that gets called from the main app.
        """
        page = cls()
        page.render() 