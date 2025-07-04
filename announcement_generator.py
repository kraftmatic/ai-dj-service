import requests
import json
import logging
import feedparser
import random
from bs4 import BeautifulSoup

class AnnouncementGenerator:
    """Generates DJ announcements using Ollama LLM"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llamusic/llamusic:latest"):
        self.ollama_url = ollama_url
        self.model = model
        self.logger = logging.getLogger(__name__)
        self.news_rss_url = "https://feedx.net/rss/ap.xml"
        self.news_cache = []  # Cache news stories to avoid repeated fetches
        self.news_cache_time = 0  # Track when cache was last updated
        
    def generate_introduction(self, song_title: str, artist: str) -> str:
        """
        Generate a 40-word introduction for the given song and artist
        """
        prompt = f"""You are a professional radio DJ. Create an engaging introduction for the song "{song_title}" by {artist} that is around 50 words. 
        
        Try to incorporate any interestings facts known about the band or song. At the end of the intro mention the stations name:  cane bay radio. 
                
        Song: {song_title}
        Artist: {artist}
        
        Generate approximately 50 words:"""
        
        try:
            response = self._call_ollama(prompt)
            introduction = self._clean_response(response)
            
            # Ensure it's roughly 40 words
            words = introduction.split()
            if len(words) > 70:
                introduction = ' '.join(words[:40])
            elif len(words) < 35:
                # If too short, try again with a different approach
                fallback_prompt = f"""Create a brief, energetic radio DJ introduction for "{song_title}" by {artist}. Make it around 50 words and sound natural."""
                response = self._call_ollama(fallback_prompt)
                introduction = self._clean_response(response)
                words = introduction.split()
                if len(words) > 40:
                    introduction = ' '.join(words[:40])
            
            self.logger.info(f"Generated introduction ({len(introduction.split())} words): {introduction}")
            return introduction
            
        except Exception as e:
            self.logger.error(f"Failed to generate introduction: {e}")
            # Fallback introduction
            return f"Here's a fantastic track from {artist}. You're about to hear {song_title}, a song that never fails to get the crowd moving. Turn it up and enjoy this one!"
    
    def _call_ollama(self, prompt: str) -> str:
        """Make API call to Ollama"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "max_tokens": 100
            }
        }
        
        response = requests.post(
            f"{self.ollama_url}/api/generate",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('response', '')
        else:
            raise Exception(f"Ollama API call failed: {response.status_code} - {response.text}")
    
    def _clean_response(self, response: str) -> str:
        """Clean up the LLM response"""
        # Remove any quotes or extra formatting
        cleaned = response.strip()
        if cleaned.startswith('"') and cleaned.endswith('"'):
            cleaned = cleaned[1:-1]
        
        # Remove any prefixes like "Here's a 40-word introduction:"
        if ":" in cleaned and len(cleaned.split(":")[0]) < 50:
            cleaned = ":".join(cleaned.split(":")[1:]).strip()
        
        return cleaned
    
    def generate_news_announcement(self, song_title: str, artist: str) -> str:
        """
        Generate a news announcement followed by music transition
        """
        try:
            # Get a random news story
            news_story = self._get_random_news_story()
            if not news_story:
                self.logger.warning("No news story available, using fallback")
                return self._generate_fallback_news_announcement(song_title, artist)
            
            # Generate 100-word synopsis using AI
            synopsis = self._generate_news_synopsis(news_story)
            
            # Create transition to music
            music_transition = self._generate_music_transition(song_title, artist)
            
            # Combine news synopsis with music transition
            full_announcement = f"{synopsis} {music_transition}"
            
            self.logger.info(f"Generated news announcement ({len(full_announcement.split())} words)")
            return full_announcement
            
        except Exception as e:
            self.logger.error(f"Failed to generate news announcement: {e}")
            return self._generate_fallback_news_announcement(song_title, artist)
    
    def _get_random_news_story(self) -> dict:
        """Fetch and return a random news story from RSS feed"""
        import time
        
        # Check if cache is still fresh (refresh every 30 minutes)
        current_time = time.time()
        if not self.news_cache or (current_time - self.news_cache_time) > 1800:
            try:
                self.logger.info(f"Fetching news from {self.news_rss_url}")
                feed = feedparser.parse(self.news_rss_url)
                
                if feed.entries:
                    self.news_cache = []
                    for entry in feed.entries[:20]:  # Take first 20 stories
                        # Clean up the description/summary
                        description = entry.get('description', '') or entry.get('summary', '')
                        if description:
                            # Remove HTML tags
                            soup = BeautifulSoup(description, 'html.parser')
                            clean_description = soup.get_text().strip()
                        else:
                            clean_description = ""
                        
                        story = {
                            'title': entry.get('title', 'News Update'),
                            'description': clean_description,
                            'link': entry.get('link', ''),
                            'published': entry.get('published', '')
                        }
                        self.news_cache.append(story)
                    
                    self.news_cache_time = current_time
                    self.logger.info(f"Cached {len(self.news_cache)} news stories")
                else:
                    self.logger.warning("No news entries found in RSS feed")
                    
            except Exception as e:
                self.logger.error(f"Failed to fetch news: {e}")
                return None
        
        # Return random story from cache
        if self.news_cache:
            return random.choice(self.news_cache)
        return None
    
    def _generate_news_synopsis(self, news_story: dict) -> str:
        """Generate a 100-word news synopsis using AI"""
        title = news_story.get('title', '')
        description = news_story.get('description', '')
        
        prompt = f"""You are a professional radio news announcer. Create a concise, informative 100-word news summary for radio broadcast.
        
        News Story Title: {title}
        News Details: {description}
        
        Create a professional, clear 100-word radio news summary. Keep it engaging but factual. Start with something like "In the news today," or "Breaking news," or "Here's what's happening in the world."
        
        Generate exactly 100 words:"""
        
        try:
            response = self._call_ollama(prompt)
            synopsis = self._clean_response(response)
            
            # Ensure it's roughly 100 words
            words = synopsis.split()
            if len(words) > 110:
                synopsis = ' '.join(words[:100])
            elif len(words) < 90:
                # If too short, try with the description included
                fallback_prompt = f"""Create a 100-word radio news summary about: {title}. {description[:200]}. Make it sound professional and radio-ready."""
                response = self._call_ollama(fallback_prompt)
                synopsis = self._clean_response(response)
                words = synopsis.split()
                if len(words) > 100:
                    synopsis = ' '.join(words[:100])
            
            return synopsis
            
        except Exception as e:
            self.logger.error(f"Failed to generate news synopsis: {e}")
            return f"In the news today: {title}. For more details on this developing story, stay tuned to your trusted news sources."
    
    def _generate_music_transition(self, song_title: str, artist: str) -> str:
        """Generate transition from news back to music"""
        transitions = [
            f"Now let's get back to the music with {song_title} by {artist}.",
            f"And now, back to the tunes - here's {song_title} by {artist}.",
            f"That's your news update. Now let's turn up the volume with {song_title} by {artist}.",
            f"Now back to our regular programming with {song_title} by {artist}.",
            f"Time to get back to the music. Here's {song_title} by {artist}.",
            f"And now, let's continue with some great music - {song_title} by {artist}.",
            f"Back to the beats with {song_title} by {artist}."
        ]
        
        return random.choice(transitions)
    
    def _generate_fallback_news_announcement(self, song_title: str, artist: str) -> str:
        """Generate fallback news announcement when RSS feed is unavailable"""
        fallback_news = [
            "Stay informed with the latest news updates throughout the day.",
            "Keep up with current events and breaking news as it happens.",
            "For the latest news and weather updates, stay tuned to your local news sources.",
            "Remember to stay connected with what's happening in your community and around the world."
        ]
        
        news_part = random.choice(fallback_news)
        music_transition = self._generate_music_transition(song_title, artist)
        
        return f"{news_part} {music_transition}"
