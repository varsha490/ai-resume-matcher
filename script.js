function generateJD() {
  const role = document.getElementById("roleSelect").value;

  if (!role) {
    alert("Please select a role");
    return;
  }

  fetch("/auto-jd", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role })
  })
  .then(res => res.json())
  .then(d => {
    document.getElementById("jdBox").value = d.job_description || "";
  });
}

document.getElementById("analyzeForm").onsubmit = async function (e) {
  e.preventDefault();

  const formData = new FormData(this);

  const res = await fetch("/analyze", {
    method: "POST",
    body: formData
  });

  const d = await res.json();

  // Show dashboard
  document.getElementById("dashboard").classList.remove("hidden");

  // Basic details
  document.getElementById("domain").innerText = d.Domain || "-";
  document.getElementById("ats").innerText = d.ATS_Score || "0%";
  document.getElementById("fit").innerText = d.Role_Fit || "-";

  // Skills
  fillTags("matched", d.Matched_Skills || []);
  fillTags("missing", d.Missing_Skills || []);

  // Interview tips
  fillList("interview", d.Interview_Tips || []);

  // Skill gap chart
  drawSkillGapChart(d.Matched_Skills || [], d.Missing_Skills || []);
};

/* ---------- Helpers ---------- */

function fillTags(id, items) {
  const el = document.getElementById(id);
  el.innerHTML = "";

  if (items.length === 0) {
    el.innerHTML = "<i>No data</i>";
    return;
  }

  items.forEach(item => {
    el.innerHTML += `<span>${item}</span>`;
  });
}

function fillList(id, items) {
  const ul = document.getElementById(id);
  ul.innerHTML = "";

  if (items.length === 0) {
    ul.innerHTML = "<li>No suggestions</li>";
    return;
  }

  items.forEach(i => {
    ul.innerHTML += `<li>${i}</li>`;
  });
}

/* ---------- Skill Gap Chart ---------- */

function drawSkillGapChart(matched, missing) {
  const canvas = document.getElementById("skillChart");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const matchedCount = matched.length;
  const missingCount = missing.length;
  const max = Math.max(matchedCount, missingCount, 1);

  const barWidth = 80;
  const baseY = 170;
  const scale = 120 / max;

  // Matched bar (green)
  ctx.fillStyle = "#10b981";
  ctx.fillRect(80, baseY - matchedCount * scale, barWidth, matchedCount * scale);
  ctx.fillStyle = "#000";
  ctx.fillText("Matched", 95, 195);
  ctx.fillText(matchedCount, 115, baseY - matchedCount * scale - 5);

  // Missing bar (red)
  ctx.fillStyle = "#ef4444";
  ctx.fillRect(220, baseY - missingCount * scale, barWidth, missingCount * scale);
  ctx.fillStyle = "#000";
  ctx.fillText("Missing", 235, 195);
  ctx.fillText(missingCount, 255, baseY - missingCount * scale - 5);
}
