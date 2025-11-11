# AbleToCompete MVP - Demo Video Script

## Pre-Recording Checklist
- [ ] Backend running on http://localhost:8005
- [ ] Frontend running on http://localhost:3000
- [ ] Browser ready (Chrome/Firefox recommended)
- [ ] Screen recording software ready
- [ ] Close unnecessary browser tabs
- [ ] Set browser zoom to 100%

## Screen Recording Tools (Choose One)

### Linux Options:
1. **OBS Studio** (Recommended - Free & Professional)
   ```bash
   sudo dnf install obs-studio  # For Fedora
   ```

2. **SimpleScreenRecorder** (Easy to use)
   ```bash
   sudo dnf install simplescreenrecorder
   ```

3. **Kazam** (Lightweight)
   ```bash
   sudo dnf install kazam
   ```

4. **FFmpeg** (Command line)
   ```bash
   ffmpeg -video_size 1920x1080 -framerate 30 -f x11grab -i :0.0 output.mp4
   ```

## Demo Script (5-7 minutes)

### Part 1: Introduction (30 seconds)
**Action:** Show the login page
**Script:**
> "Welcome to AbleToCompete MVP - a comprehensive task management and monitoring platform built for the 100K challenge. This application combines project management with real-time monitoring capabilities."

**URL:** http://localhost:3000/login

---

### Part 2: Authentication (30 seconds)
**Action:** Login to the application
**Script:**
> "Let's start by logging in. The MVP uses JWT-based authentication for secure access."

**Steps:**
1. Enter email: `test@example.com`
2. Enter password: `password123`
3. Click "Login"

---

### Part 3: Dashboard Overview (1 minute)
**Action:** Explore the dashboard
**Script:**
> "Here's the main dashboard with an overview of key metrics. We can see:
> - Active tasks across all boards
> - Monitoring status of our services
> - Recent activity feed
> - Quick access to all main features through the top navigation"

**Highlight:**
- Beautiful Bootstrap 5 UI with custom theme
- Responsive design
- Modern gradient cards
- Activity timeline

---

### Part 4: Task Board - View Board (1.5 minutes)
**Action:** Navigate to Task Board
**Script:**
> "Let's check out the Task Board - a Kanban-style project management interface."

**Steps:**
1. Click "Task Board" in navigation
2. Show the existing "pokus" board
3. Click on "pokus" to open it

**Highlight:**
> "We can see our board with multiple lists - 'list 1' with one card, and 'To Do' with our authentication task. This is a real-time view showing all tasks organized by status."

---

### Part 5: Task Board - Create List (1 minute)
**Action:** Create a new list
**Script:**
> "Let's add a new list to organize our workflow better. I'll create an 'In Progress' list."

**Steps:**
1. Click "Add List" button
2. Enter name: "In Progress"
3. Click "Create List"
4. Show that it appears immediately (no page refresh needed!)

**Highlight:**
> "Notice how the list appears instantly - that's React Query automatically updating the UI."

---

### Part 6: Task Board - Create Cards (1.5 minutes)
**Action:** Create new cards
**Script:**
> "Now let's add some tasks. I'll create a couple of cards to demonstrate the workflow."

**Steps:**
1. In "To Do" list, click "+ Add a card"
2. Enter: "Design database schema"
3. Create another: "Setup CI/CD pipeline"
4. In "In Progress" list, create: "Implement monitoring dashboard"

**Highlight:**
> "Each card appears immediately, demonstrating the reactive nature of the application. The nested API response we built ensures all data stays in sync."

---

### Part 7: Monitoring Dashboard (1 minute)
**Action:** Navigate to Monitoring
**Script:**
> "The monitoring section allows you to track the health of your services in real-time."

**Steps:**
1. Click "Monitoring" in navigation
2. Show the monitoring overview
3. Explain the features (even if minimal data)

**Highlight:**
> "This section demonstrates the application's capability to monitor multiple endpoints, track uptime, and alert on issues."

---

### Part 8: Technical Features Highlight (1 minute)
**Action:** Stay on monitoring or go back to dashboard
**Script:**
> "Let me highlight the technical features of this MVP:
>
> **Backend:**
> - FastAPI with async/await for high performance
> - PostgreSQL database with SQLAlchemy ORM
> - JWT authentication
> - RESTful API with automatic OpenAPI documentation
> - Nested response models for efficient data fetching
>
> **Frontend:**
> - React 18 with TypeScript
> - Bootstrap 5 with custom theme
> - React Query for state management and caching
> - React Router for navigation
> - Responsive design that works on all devices
>
> **Architecture:**
> - Clean separation of concerns
> - Async database operations
> - Real-time UI updates
> - Scalable and maintainable codebase"

---

### Part 9: User Experience Features (30 seconds)
**Action:** Show navigation and responsive features
**Script:**
> "The UI features include:
> - Smooth animations and transitions
> - Custom scrollbars
> - Notification bell (UI ready for future implementation)
> - User dropdown with profile options
> - Beautiful gradient cards with hover effects"

**Demo:**
1. Hover over cards to show shadow effect
2. Open user dropdown
3. Show navigation highlighting

---

### Part 10: Conclusion (30 seconds)
**Action:** Return to dashboard
**Script:**
> "AbleToCompete MVP successfully demonstrates:
> - Full-stack development with modern technologies
> - Clean, professional UI/UX design
> - Real-time data synchronization
> - Scalable architecture ready for production
>
> This MVP is built for the 100K challenge and showcases enterprise-grade development practices. Thank you for watching!"

---

## Post-Recording Checklist
- [ ] Review the recording for audio/video quality
- [ ] Trim any unnecessary parts
- [ ] Add title slide (optional)
- [ ] Add background music (optional, keep it subtle)
- [ ] Export in high quality (1080p recommended)

## Video Export Settings
- **Resolution:** 1920x1080 (1080p)
- **Frame Rate:** 30 fps
- **Format:** MP4 (H.264)
- **Bitrate:** 8-10 Mbps

## Additional Tips
1. **Practice First:** Do a dry run before recording
2. **Speak Clearly:** Use a good microphone if possible
3. **Steady Pace:** Don't rush, let viewers see each feature
4. **Show, Don't Tell:** Let the UI speak for itself
5. **Have Fun:** Your enthusiasm will show!

## Quick Reference - URLs
- Frontend: http://localhost:3000
- Backend API Docs: http://localhost:8005/docs
- Login: test@example.com / password123

## Troubleshooting
If you encounter issues during recording:
- Refresh the browser if UI seems unresponsive
- Check backend logs: Backend is running in terminal
- Check frontend logs: Frontend is running in terminal
- Clear browser cache if needed: Ctrl+Shift+Delete
