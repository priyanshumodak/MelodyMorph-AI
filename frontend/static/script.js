async function generateAI() {
    const res = await fetch('/generate_ai');
    const data = await res.json();
    console.log("AI Output:", data);
    alert("AI music generated! Check console.");
}