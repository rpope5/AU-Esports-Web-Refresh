"use client"

import { useEffect, useState } from "react"
import FullCalendar from "@fullcalendar/react"
import dayGridPlugin from "@fullcalendar/daygrid"

export default function Calendar() {
  const [events, setEvents] = useState([])

  useEffect(() => {
    fetch("/api/calendar/events")
      .then(res => res.json())
      .then(data => setEvents(data))
  }, [])

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <FullCalendar
        plugins={[dayGridPlugin]}
        initialView="dayGridMonth"
        events={events}
        height="auto"
        editable={false}
        selectable={false}
      />
    </div>
  )
}