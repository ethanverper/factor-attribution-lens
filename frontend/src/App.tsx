import { BrowserRouter, Route, Routes } from "react-router-dom"
import { ThemeProvider } from "@/components/theme-provider"
import { AppLayout } from "@/components/AppLayout"
import { Overview } from "@/pages/Overview"
import { Inputs } from "@/pages/Inputs"
import { Results } from "@/pages/Results"
import { Learning } from "@/pages/Learning"
import { Glossary } from "@/pages/Glossary"
import { Tools } from "@/pages/Tools"
import { References } from "@/pages/References"
import { RealWorld } from "@/pages/RealWorld"

function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<Overview />} />
            <Route path="/inputs" element={<Inputs />} />
            <Route path="/results" element={<Results />} />
            <Route path="/learning" element={<Learning />} />
            <Route path="/glossary" element={<Glossary />} />
            <Route path="/tools" element={<Tools />} />
            <Route path="/references" element={<References />} />
            <Route path="/real-world" element={<RealWorld />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  )
}

export default App
