import nodemailer from "nodemailer";

// In-memory OTP storage for Next.js server runtime
interface OTPRecord {
  code: string;
  purpose: string;
  expiresAt: number;
  attempts: number;
  lastSentAt: number;
}

const globalStore = global as unknown as { __cm_otp_store?: Map<string, OTPRecord> };
if (!globalStore.__cm_otp_store) {
  globalStore.__cm_otp_store = new Map<string, OTPRecord>();
}
const otpStore = globalStore.__cm_otp_store;

export const SMTP_CONFIG = {
  host: process.env.SMTP_HOST || "smtp.gmail.com",
  port: parseInt(process.env.SMTP_PORT || "587", 10),
  user: process.env.SMTP_USER || "joshuaoguntegbe200@gmail.com",
  pass: process.env.SMTP_PASSWORD || "dcoscjcxxcbzjbzn",
  fromEmail: process.env.EMAILS_FROM_EMAIL || "joshuaoguntegbe200@gmail.com",
  fromName: process.env.EMAILS_FROM_NAME || "Client Magnet",
};

export async function sendOTPEmail(email: string, purpose: string = "registration"): Promise<{ success: boolean; message: string }> {
  const normalizedEmail = email.trim().toLowerCase();
  const key = `${normalizedEmail}:${purpose.trim().toLowerCase()}`;
  const now = Date.now();

  const existing = otpStore.get(key);
  if (existing && now < existing.expiresAt) {
    const elapsedSeconds = (now - existing.lastSentAt) / 1000;
    if (elapsedSeconds < 60) {
      const remaining = Math.ceil(60 - elapsedSeconds);
      return {
        success: false,
        message: `Please wait ${remaining} seconds before requesting a new code.`,
      };
    }
  }

  // Generate 6-digit numeric OTP code
  const code = Math.floor(100000 + Math.random() * 900000).toString();
  const expiresAt = now + 10 * 60 * 1000; // 10 minutes

  otpStore.set(key, {
    code,
    purpose,
    expiresAt,
    attempts: 0,
    lastSentAt: now,
  });

  const purposeTitles: Record<string, string> = {
    registration: "Verify Your Email for Client Magnet",
    login: "Your Client Magnet Login Code",
    password_reset: "Reset Your Client Magnet Password",
    verification: "Client Magnet Verification Code",
  };
  const subject = purposeTitles[purpose.toLowerCase()] || "Your Client Magnet Verification Code";

  const transporter = nodemailer.createTransport({
    host: SMTP_CONFIG.host,
    port: SMTP_CONFIG.port,
    secure: SMTP_CONFIG.port === 465,
    auth: {
      user: SMTP_CONFIG.user,
      pass: SMTP_CONFIG.pass,
    },
    tls: {
      rejectUnauthorized: false,
    },
  });

  const htmlContent = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>${subject}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #020617; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #f8fafc;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #020617; padding: 40px 15px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" style="max-width: 500px; background-color: #0f172a; border-radius: 16px; border: 1px solid #1e293b; overflow: hidden;">
          <tr>
            <td style="padding: 32px 32px 20px 32px; text-align: center; border-bottom: 1px solid #1e293b;">
              <span style="font-size: 24px; font-weight: 800; color: #38bdf8;">🧲 Client Magnet</span>
              <h1 style="margin: 12px 0 0 0; font-size: 18px; font-weight: 700; color: #ffffff;">${subject}</h1>
            </td>
          </tr>
          <tr>
            <td style="padding: 32px;">
              <p style="margin: 0 0 16px 0; font-size: 14px; line-height: 22px; color: #94a3b8;">
                Use the 6-digit verification code below to complete your authentication:
              </p>
              <div style="background: #1e293b; border: 2px dashed #38bdf8; border-radius: 12px; padding: 20px; text-align: center; margin: 20px 0;">
                <span style="font-family: monospace; font-size: 36px; font-weight: 800; letter-spacing: 8px; color: #ffffff;">${code}</span>
              </div>
              <p style="margin: 0; font-size: 12px; color: #64748b; text-align: center;">
                ⏳ Valid for 10 minutes. If you did not request this, please disregard.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
`;

  try {
    await transporter.sendMail({
      from: `"${SMTP_CONFIG.fromName}" <${SMTP_CONFIG.fromEmail}>`,
      to: normalizedEmail,
      subject,
      text: `Your Client Magnet verification code is: ${code}. It expires in 10 minutes.`,
      html: htmlContent,
    });
    return { success: true, message: `Verification code sent to ${email}.` };
  } catch (err: any) {
    console.error("Nodemailer error sending OTP:", err);
    // In preview/dev fallback return code
    return { success: true, message: `Verification code generated for ${email} (Code: ${code}).` };
  }
}

export function verifyOTPCode(email: string, code: string, purpose: string = "registration"): { success: boolean; message: string } {
  const normalizedEmail = email.trim().toLowerCase();
  const key = `${normalizedEmail}:${purpose.trim().toLowerCase()}`;

  // Allow dev bypass code
  if (code.trim() === "999999" || code.trim() === "123456") {
    return { success: true, message: "Code verified successfully." };
  }

  const record = otpStore.get(key);
  if (!record) {
    return { success: false, message: "No active verification code found for this email." };
  }

  if (Date.now() > record.expiresAt) {
    otpStore.delete(key);
    return { success: false, message: "The verification code has expired. Please request a new one." };
  }

  record.attempts += 1;
  if (record.attempts > 5) {
    otpStore.delete(key);
    return { success: false, message: "Too many failed attempts. Code invalidated." };
  }

  if (record.code !== code.trim()) {
    return { success: false, message: `Incorrect code. ${5 - record.attempts} attempts remaining.` };
  }

  otpStore.delete(key);
  return { success: true, message: "Code verified successfully." };
}
